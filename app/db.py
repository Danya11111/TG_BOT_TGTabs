from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS kb_articles (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    question_norm TEXT NOT NULL,
    summary TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    docs_links_json TEXT NOT NULL,
    video_links_json TEXT NOT NULL,
    category TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    aliases_json TEXT NOT NULL,
    related_ids_json TEXT NOT NULL,
    answer_version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kb_question_norm ON kb_articles(question_norm);
CREATE INDEX IF NOT EXISTS idx_kb_category ON kb_articles(category);
CREATE INDEX IF NOT EXISTS idx_kb_status ON kb_articles(status);

CREATE TABLE IF NOT EXISTS kb_unknown_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    chat_id INTEGER,
    is_group INTEGER NOT NULL,
    question TEXT NOT NULL,
    question_norm TEXT NOT NULL,
    category_hint TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_unknown_question_norm ON kb_unknown_questions(question_norm);

CREATE TABLE IF NOT EXISTS group_question_dedup (
    dedup_key TEXT PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    question_norm TEXT NOT NULL,
    expires_at_epoch INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_group_dedup_expires ON group_question_dedup(expires_at_epoch);

CREATE TABLE IF NOT EXISTS user_last_answer (
    user_id INTEGER PRIMARY KEY,
    article_id TEXT NOT NULL,
    question_norm TEXT NOT NULL,
    answered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    chat_id INTEGER,
    is_group INTEGER NOT NULL,
    question TEXT NOT NULL,
    question_norm TEXT NOT NULL,
    matched_article_id TEXT,
    score REAL,
    match_reason TEXT,
    category TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_question_norm ON query_logs(question_norm);
"""


async def ensure_db(sqlite_path: str) -> None:
    path = Path(sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path.as_posix()) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()


async def fetch_all_articles(sqlite_path: str) -> list[dict[str, Any]]:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM kb_articles WHERE status IN ('active','deprecated')"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
    return [dict(x) for x in rows]


async def upsert_articles(sqlite_path: str, articles: list[dict[str, Any]]) -> int:
    if not articles:
        return 0
    now = utc_now_iso()
    payload = []
    for a in articles:
        payload.append(
            (
                a["id"],
                a["question"],
                a["question_norm"],
                a["summary"],
                json.dumps(a.get("steps", []), ensure_ascii=False),
                json.dumps(a.get("docs_links", []), ensure_ascii=False),
                json.dumps(a.get("video_links", []), ensure_ascii=False),
                a.get("category", "general"),
                json.dumps(a.get("tags", []), ensure_ascii=False),
                json.dumps(a.get("aliases", []), ensure_ascii=False),
                json.dumps(a.get("related_ids", []), ensure_ascii=False),
                int(a.get("answer_version", 1)),
                a.get("status", "active"),
                a.get("valid_from", now),
                a.get("valid_to"),
                a.get("source", "manual"),
                now,
            )
        )
    sql = """
    INSERT INTO kb_articles (
      id, question, question_norm, summary, steps_json, docs_links_json, video_links_json,
      category, tags_json, aliases_json, related_ids_json, answer_version, status, valid_from,
      valid_to, source, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      question=excluded.question,
      question_norm=excluded.question_norm,
      summary=excluded.summary,
      steps_json=excluded.steps_json,
      docs_links_json=excluded.docs_links_json,
      video_links_json=excluded.video_links_json,
      category=excluded.category,
      tags_json=excluded.tags_json,
      aliases_json=excluded.aliases_json,
      related_ids_json=excluded.related_ids_json,
      answer_version=excluded.answer_version,
      status=excluded.status,
      valid_from=excluded.valid_from,
      valid_to=excluded.valid_to,
      source=excluded.source,
      updated_at=excluded.updated_at
    """
    async with aiosqlite.connect(sqlite_path) as db:
        await db.executemany(sql, payload)
        await db.commit()
    return len(payload)


async def get_article_by_id(sqlite_path: str, article_id: str) -> dict[str, Any] | None:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM kb_articles WHERE id = ?", (article_id,))
        row = await cursor.fetchone()
    return dict(row) if row else None


async def set_user_last_answer(sqlite_path: str, user_id: int, article_id: str, question_norm: str) -> None:
    sql = """
    INSERT INTO user_last_answer (user_id, article_id, question_norm, answered_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
      article_id=excluded.article_id,
      question_norm=excluded.question_norm,
      answered_at=excluded.answered_at
    """
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(sql, (user_id, article_id, question_norm, utc_now_iso()))
        await db.commit()


async def get_user_last_answer(sqlite_path: str, user_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM user_last_answer WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
    return dict(row) if row else None


async def log_query_event(
    sqlite_path: str,
    *,
    user_id: int | None,
    chat_id: int | None,
    is_group: bool,
    question: str,
    question_norm: str,
    matched_article_id: str | None,
    score: float | None,
    match_reason: str | None,
    category: str | None,
) -> None:
    sql = """
    INSERT INTO query_logs (
      user_id, chat_id, is_group, question, question_norm, matched_article_id, score, match_reason, category, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    async with aiosqlite.connect(sqlite_path) as db:
        await db.execute(
            sql,
            (
                user_id,
                chat_id,
                1 if is_group else 0,
                question.strip(),
                question_norm,
                matched_article_id,
                score,
                match_reason,
                category,
                utc_now_iso(),
            ),
        )
        await db.commit()


async def get_analytics_snapshot(sqlite_path: str, *, window_days: int = 30) -> dict[str, Any]:
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        since_expr = f"datetime('now', '-{int(window_days)} days')"

        total_query = f"SELECT COUNT(*) AS c FROM query_logs WHERE datetime(created_at) >= {since_expr}"
        total = (await (await db.execute(total_query)).fetchone())["c"]

        top_query = f"""
        SELECT question_norm, COUNT(*) AS c
        FROM query_logs
        WHERE datetime(created_at) >= {since_expr}
        GROUP BY question_norm
        ORDER BY c DESC
        LIMIT 10
        """
        top_rows = await (await db.execute(top_query)).fetchall()

        latest_query = f"""
        SELECT question, question_norm, matched_article_id, created_at, is_group
        FROM query_logs
        WHERE datetime(created_at) >= {since_expr}
        ORDER BY id DESC
        LIMIT 10
        """
        latest_rows = await (await db.execute(latest_query)).fetchall()

        unknown_query = f"""
        SELECT COUNT(*) AS c
        FROM query_logs
        WHERE datetime(created_at) >= {since_expr} AND matched_article_id IS NULL
        """
        unknown_count = (await (await db.execute(unknown_query)).fetchone())["c"]

        group_query = f"""
        SELECT
          SUM(CASE WHEN is_group = 1 THEN 1 ELSE 0 END) AS group_count,
          SUM(CASE WHEN is_group = 0 THEN 1 ELSE 0 END) AS private_count
        FROM query_logs
        WHERE datetime(created_at) >= {since_expr}
        """
        group_row = await (await db.execute(group_query)).fetchone()

        category_query = f"""
        SELECT COALESCE(category, 'unknown') AS category, COUNT(*) AS c
        FROM query_logs
        WHERE datetime(created_at) >= {since_expr}
        GROUP BY COALESCE(category, 'unknown')
        ORDER BY c DESC
        LIMIT 5
        """
        category_rows = await (await db.execute(category_query)).fetchall()

    return {
        "window_days": window_days,
        "total": int(total or 0),
        "unknown_count": int(unknown_count or 0),
        "group_count": int((group_row["group_count"] if group_row else 0) or 0),
        "private_count": int((group_row["private_count"] if group_row else 0) or 0),
        "top10": [dict(x) for x in top_rows],
        "latest10": [dict(x) for x in latest_rows],
        "top_categories": [dict(x) for x in category_rows],
    }

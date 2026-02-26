from __future__ import annotations

import json
from pathlib import Path

from app.db import upsert_articles
from app.parsers.normalize import normalize_text


def load_json_articles(path: str) -> list[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("KB seed file must contain JSON list.")

    out: list[dict] = []
    for item in raw:
        question = item["question"].strip()
        out.append(
            {
                "id": item["id"],
                "question": question,
                "question_norm": normalize_text(question),
                "summary": item["summary"].strip(),
                "steps": item.get("steps", []),
                "docs_links": item.get("docs_links", []),
                "video_links": item.get("video_links", []),
                "category": item.get("category", "general"),
                "tags": item.get("tags", []),
                "aliases": [normalize_text(x) for x in item.get("aliases", [])],
                "related_ids": item.get("related_ids", []),
                "answer_version": int(item.get("answer_version", 1)),
                "status": item.get("status", "active"),
                "valid_from": item.get("valid_from"),
                "valid_to": item.get("valid_to"),
                "source": item.get("source", "manual"),
            }
        )
    return out


async def load_seed_to_db(sqlite_path: str, seed_path: str) -> int:
    items = load_json_articles(seed_path)
    return await upsert_articles(sqlite_path, items)

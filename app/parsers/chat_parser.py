from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from app.parsers.normalize import looks_like_question, normalize_text


def _extract_messages(html_path: Path) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    out: list[dict[str, Any]] = []
    for msg in soup.select("div.message.default.clearfix"):
        msg_id = msg.get("id", "")
        text_node = msg.select_one("div.text")
        from_node = msg.select_one("div.from_name")
        if not text_node or not from_node:
            continue
        reply_node = msg.select_one("div.reply_to.details a")
        reply_ref = None
        if reply_node and reply_node.get("href", "").startswith("#go_to_message"):
            reply_ref = reply_node.get("href", "").replace("#go_to_message", "message")
        out.append(
            {
                "id": msg_id,
                "author": from_node.get_text(" ", strip=True),
                "text": text_node.get_text(" ", strip=True),
                "reply_ref": reply_ref,
            }
        )
    return out


def build_qa_from_exports(export_dir: str, support_usernames: set[str]) -> list[dict[str, Any]]:
    paths = sorted(Path(export_dir).glob("messages*.html"))
    if not paths:
        return []

    messages: list[dict[str, Any]] = []
    for p in paths:
        messages.extend(_extract_messages(p))

    by_id = {m["id"]: m for m in messages if m["id"]}
    articles: list[dict[str, Any]] = []

    for msg in messages:
        q_text = msg["text"]
        if not looks_like_question(q_text):
            continue
        q_author = msg["author"].strip().lower().lstrip("@")
        if q_author in support_usernames:
            continue

        answer = None
        for candidate in messages:
            cand_author = candidate["author"].strip().lower().lstrip("@")
            if cand_author not in support_usernames:
                continue
            if candidate.get("reply_ref") == msg["id"]:
                answer = candidate
                break

        if not answer and msg.get("reply_ref"):
            replied = by_id.get(msg["reply_ref"])
            if replied:
                for candidate in messages:
                    cand_author = candidate["author"].strip().lower().lstrip("@")
                    if cand_author in support_usernames and candidate.get("reply_ref") == replied.get("id"):
                        answer = candidate
                        break

        # Fallback mode for exports where support usernames are unknown.
        if not answer:
            for candidate in messages:
                if candidate.get("reply_ref") != msg["id"]:
                    continue
                if candidate["author"].strip().lower() == msg["author"].strip().lower():
                    continue
                if looks_like_question(candidate["text"]):
                    continue
                answer = candidate
                break

        if not answer:
            continue

        q_norm = normalize_text(q_text)
        base = f"{q_norm}|{answer['text']}"
        aid = "chat_" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

        articles.append(
            {
                "id": aid,
                "question": q_text,
                "question_norm": q_norm,
                "summary": answer["text"][:280],
                "steps": [answer["text"]],
                "docs_links": [],
                "video_links": [],
                "category": "community",
                "tags": ["chat", "support"],
                "aliases": [q_norm],
                "related_ids": [],
                "answer_version": 1,
                "status": "active",
                "source": "chat",
            }
        )
    return _deduplicate_articles(articles)


def _deduplicate_articles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = item["question_norm"]
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out

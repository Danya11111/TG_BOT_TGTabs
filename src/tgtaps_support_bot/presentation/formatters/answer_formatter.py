from __future__ import annotations

import json
import re

from tgtaps_support_bot.domain.services.search_engine import SearchResult


_OLD_DOCS_PREFIX = "https://docs.tgtaps.com/tgtaps-docs"
_NEW_DOCS_PREFIX = "https://tgtaps.gitbook.io/tgtaps-docs"
_URL_RE = re.compile(r"https?://[^\s)>\]]+")


def _normalize_docs_urls(text: str) -> str:
    return text.replace(_OLD_DOCS_PREFIX, _NEW_DOCS_PREFIX)


def _split_into_steps(raw_text: str) -> list[str]:
    text = raw_text.strip()
    if not text:
        return []
    chunks = [x.strip(" -") for x in re.split(r"(?<=[.!?])\s+|\s+-\s+", text) if x.strip()]
    if len(chunks) > 1:
        return chunks[:5]
    return [text]


def _extract_doc_urls(*texts: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for text in texts:
        for url in _URL_RE.findall(text):
            normalized = _normalize_docs_urls(url.rstrip(".,);"))
            if "gitbook.io/tgtaps-docs" not in normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            links.append({"title": "TgTaps Docs", "url": normalized})
    return links


def format_full_answer(primary: dict, similar: list[SearchResult], previous_article_id: str | None = None) -> str:
    summary = _normalize_docs_urls(primary["summary"])
    steps = [_normalize_docs_urls(step) for step in json.loads(primary["steps_json"])]
    docs_links = json.loads(primary["docs_links_json"])
    video_links = json.loads(primary["video_links_json"])
    docs_links = [{**link, "url": _normalize_docs_urls(link["url"])} for link in docs_links if link.get("url")]

    if not steps:
        steps = [summary]
    if len(steps) == 1 and steps[0].strip() == summary.strip():
        steps = _split_into_steps(steps[0])
    elif len(steps) == 1 and len(steps[0]) > 180:
        steps = _split_into_steps(steps[0])

    lines: list[str] = [f"📌 {summary}", ""]

    lines.append("✅ Пошаговая инструкция:")
    for i, step in enumerate(steps, start=1):
        lines.append(f"{i}. {step}")

    docs_links = docs_links + _extract_doc_urls(summary, *steps)
    deduped_docs: list[dict[str, str]] = []
    seen_docs: set[str] = set()
    for link in docs_links:
        url = link.get("url", "").strip()
        if not url or url in seen_docs:
            continue
        seen_docs.add(url)
        deduped_docs.append({"title": link.get("title", "Документация"), "url": url})
    docs_links = deduped_docs

    if docs_links:
        lines.extend(["", "📚 Документация:"])
        for link in docs_links:
            lines.append(f"- {link['title']}: {link['url']}")

    if video_links:
        lines.extend(["", "🎥 Видео:"])
        for link in video_links:
            lines.append(f"- {link['title']}: {link['url']}")

    similar_questions = []
    community_example = None
    for result in similar:
        q = result.row["question"]
        if q != primary["question"]:
            similar_questions.append(q)
        if community_example is None and result.row.get("source") == "chat":
            community_example = _normalize_docs_urls(result.row.get("summary", "").strip())
    if community_example:
        lines.extend(["", "💬 Пример из чата:", community_example])
    if similar_questions:
        lines.extend(["", "🔎 Похожие вопросы:"])
        for q in similar_questions[:3]:
            lines.append(f"- {q}")

    return "\n".join(lines)


def format_group_answer(summary: str, bot_username: str) -> str:
    return (
        f"💡 {summary}\n\n"
        f"Полный ответ с шагами и ссылками: https://t.me/{bot_username}?start=support"
    )

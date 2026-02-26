from __future__ import annotations

import json

from app.search.search_engine import SearchResult


def format_full_answer(primary: dict, similar: list[SearchResult], previous_article_id: str | None = None) -> str:
    summary = primary["summary"]
    steps = json.loads(primary["steps_json"])
    docs_links = json.loads(primary["docs_links_json"])
    video_links = json.loads(primary["video_links_json"])

    lines: list[str] = [f"📌 {summary}", ""]
    if previous_article_id and previous_article_id != primary["id"]:
        lines.append(f"🔁 В продолжение прошлого ответа: `{previous_article_id}`")
        lines.append("")

    lines.append("✅ Пошаговая инструкция:")
    for i, step in enumerate(steps, start=1):
        lines.append(f"{i}. {step}")

    if docs_links:
        lines.extend(["", "📚 Документация:"])
        for link in docs_links:
            lines.append(f"- {link['title']}: {link['url']}")

    if video_links:
        lines.extend(["", "🎥 Видео:"])
        for link in video_links:
            lines.append(f"- {link['title']}: {link['url']}")

    similar_questions = []
    for result in similar:
        q = result.row["question"]
        if q != primary["question"]:
            similar_questions.append(q)
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

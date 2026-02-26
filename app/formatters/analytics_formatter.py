from __future__ import annotations


def format_analytics(snapshot: dict) -> str:
    total = snapshot["total"]
    unknown = snapshot["unknown_count"]
    private_count = snapshot["private_count"]
    group_count = snapshot["group_count"]
    window_days = snapshot["window_days"]

    unknown_rate = (unknown / total * 100.0) if total else 0.0
    lines: list[str] = [
        f"📊 Аналитика за {window_days} дн.",
        "",
        f"2) Количество запросов: {total}",
        f"   • ЛС: {private_count}",
        f"   • Группы: {group_count}",
        f"   • Unknown: {unknown} ({unknown_rate:.1f}%)",
        "",
        "1) Топ 10 запросов:",
    ]

    top10 = snapshot.get("top10", [])
    if not top10:
        lines.append("- Пока нет данных")
    else:
        for i, row in enumerate(top10, start=1):
            lines.append(f"{i}. {row['question_norm']} — {row['c']}")

    lines.extend(["", "3) Новые 10 запросов:"])
    latest10 = snapshot.get("latest10", [])
    if not latest10:
        lines.append("- Пока нет данных")
    else:
        for i, row in enumerate(latest10, start=1):
            channel = "group" if row.get("is_group") else "private"
            status = "matched" if row.get("matched_article_id") else "unknown"
            lines.append(f"{i}. [{channel}/{status}] {row['question']}")

    lines.extend(["", "4) Качественная аналитика владельца:"])
    categories = snapshot.get("top_categories", [])
    if categories:
        lines.append("   • Топ категорий:")
        for row in categories:
            lines.append(f"     - {row['category']}: {row['c']}")
    else:
        lines.append("   • Топ категорий: нет данных")

    lines.extend(
        [
            "   • Рекомендации:",
            "     - Добавить ответы для repeated unknown в топе",
            "     - Перепроверить формулировки алиасов для high-volume запросов",
            "     - Раз в неделю обновлять KB из новых чатов",
        ]
    )
    return "\n".join(lines)

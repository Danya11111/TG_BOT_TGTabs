from app.formatters.analytics_formatter import format_analytics


def test_format_analytics_contains_required_sections():
    snapshot = {
        "window_days": 30,
        "total": 25,
        "unknown_count": 5,
        "private_count": 18,
        "group_count": 7,
        "top10": [{"question_norm": "как подключить кошелек", "c": 8}],
        "latest10": [{"question": "Почему не работает?", "is_group": 0, "matched_article_id": None}],
        "top_categories": [{"category": "wallet", "c": 12}],
    }
    text = format_analytics(snapshot)
    assert "1) Топ 10 запросов" in text
    assert "2) Количество запросов" in text
    assert "3) Новые 10 запросов" in text
    assert "4) Качественная аналитика владельца" in text

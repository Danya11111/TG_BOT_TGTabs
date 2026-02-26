import json

from app.search.search_engine import SearchEngine


def _row(
    *,
    q_norm: str,
    aliases: list[str],
    category: str = "general",
    status: str = "active",
    row_id: str = "x1",
) -> dict:
    return {
        "id": row_id,
        "question": q_norm,
        "question_norm": q_norm,
        "summary": "summary",
        "steps_json": "[]",
        "docs_links_json": "[]",
        "video_links_json": "[]",
        "category": category,
        "tags_json": json.dumps(["tag"]),
        "aliases_json": json.dumps(aliases),
        "related_ids_json": "[]",
        "answer_version": 1,
        "status": status,
        "valid_from": "2026-01-01T00:00:00+00:00",
        "valid_to": None,
        "source": "manual",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


def test_exact_question_priority():
    rows = [_row(q_norm="как подключить кошелек", aliases=["wallet connect"], row_id="a1")]
    engine = SearchEngine(rows)
    res = engine.search("Как подключить кошелек?")
    assert res
    assert res[0].row["id"] == "a1"
    assert res[0].reason == "exact_question"


def test_exact_alias_priority():
    rows = [_row(q_norm="q1", aliases=["рефералка"], row_id="a2")]
    engine = SearchEngine(rows)
    res = engine.search("рефералка")
    assert res
    assert res[0].row["id"] == "a2"
    assert res[0].reason == "exact_alias"

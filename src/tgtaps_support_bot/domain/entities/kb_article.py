from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class KBArticle:
    id: str
    question: str
    question_norm: str
    summary: str
    steps_json: str
    docs_links_json: str
    video_links_json: str
    category: str
    tags_json: str
    aliases_json: str
    related_ids_json: str
    answer_version: int
    status: str
    valid_from: str
    valid_to: str | None
    source: str
    updated_at: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "KBArticle":
        return cls(**row)

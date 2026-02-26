from __future__ import annotations

import json
from dataclasses import dataclass

from rapidfuzz import fuzz

from app.parsers.normalize import normalize_text


@dataclass(slots=True)
class SearchResult:
    row: dict
    score: float
    reason: str


class SearchEngine:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.by_question_norm = {r["question_norm"]: r for r in rows}
        self.alias_to_rows: dict[str, list[dict]] = {}
        self.category_map: dict[str, list[dict]] = {}
        for row in rows:
            for alias in json.loads(row["aliases_json"]):
                self.alias_to_rows.setdefault(alias, []).append(row)
            self.category_map.setdefault(row["category"], []).append(row)

    def normalize(self, text: str) -> str:
        return normalize_text(text)

    def search(self, question: str, category_hint: str | None = None, top_k: int = 5) -> list[SearchResult]:
        qn = self.normalize(question)
        if not qn:
            return []

        # 1) Exact question
        exact = self.by_question_norm.get(qn)
        if exact:
            return [SearchResult(row=exact, score=100.0, reason="exact_question")]

        # 2) Exact alias
        alias_hits = self.alias_to_rows.get(qn, [])
        if alias_hits:
            return [SearchResult(row=x, score=90.0, reason="exact_alias") for x in alias_hits[:top_k]]

        # 3) Keywords + fuzzy
        q_tokens = set(qn.split())
        ranked: list[SearchResult] = []
        for row in self.rows:
            row_score = 0.0
            reason = "keywords_fuzzy"

            rq = row["question_norm"]
            ratio_q = fuzz.ratio(qn, rq)
            row_score += ratio_q * 0.45

            aliases = json.loads(row["aliases_json"])
            if aliases:
                alias_ratio = max(fuzz.ratio(qn, a) for a in aliases)
                row_score += alias_ratio * 0.25

            tag_tokens = set(json.loads(row["tags_json"]))
            row_tokens = set(rq.split()) | tag_tokens
            overlap = len(q_tokens & row_tokens)
            row_score += min(overlap * 6.0, 24.0)

            if category_hint and row.get("category") == category_hint:
                row_score += 5.0
                reason = "keywords_fuzzy_category"

            if row.get("status") != "active":
                row_score -= 40.0

            if row_score >= 35.0:
                ranked.append(SearchResult(row=row, score=row_score, reason=reason))

        ranked.sort(key=lambda x: x.score, reverse=True)
        if ranked:
            return ranked[:top_k]

        # 4) Category fallback
        if category_hint and category_hint in self.category_map:
            return [
                SearchResult(row=x, score=20.0, reason="category_fallback")
                for x in self.category_map[category_hint][:top_k]
            ]
        return []

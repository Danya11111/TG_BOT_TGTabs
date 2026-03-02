from __future__ import annotations

from dataclasses import dataclass

from tgtaps_support_bot.domain.services.search_engine import SearchEngine, SearchResult


@dataclass(slots=True)
class PrivateResolution:
    question_norm: str
    status: str
    results: list[SearchResult]


@dataclass(slots=True)
class GroupResolution:
    question_norm: str
    status: str
    result: SearchResult | None


def resolve_private_question(
    *,
    search_engine: SearchEngine,
    question: str,
    min_confidence: float,
    ambiguity_delta: float,
) -> PrivateResolution:
    results = search_engine.search(question)
    norm = search_engine.normalize(question)
    if not results or results[0].score < min_confidence:
        return PrivateResolution(question_norm=norm, status="not_found", results=[])
    if len(results) > 1 and (results[0].score - results[1].score) < ambiguity_delta:
        return PrivateResolution(question_norm=norm, status="ambiguous", results=results)
    return PrivateResolution(question_norm=norm, status="matched", results=results)


def resolve_group_question(
    *,
    search_engine: SearchEngine,
    question: str,
    min_confidence: float,
) -> GroupResolution:
    results = search_engine.search(question)
    norm = search_engine.normalize(question)
    if not results or results[0].score < min_confidence:
        return GroupResolution(question_norm=norm, status="not_found", result=None)
    return GroupResolution(question_norm=norm, status="matched", result=results[0])

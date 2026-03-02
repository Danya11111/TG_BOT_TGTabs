from __future__ import annotations

from tgtaps_support_bot.infrastructure.persistence.sqlite_gateway import get_analytics_snapshot
from tgtaps_support_bot.presentation.formatters.analytics_formatter import format_analytics


async def build_owner_analytics_report(sqlite_path: str, *, window_days: int = 30) -> str:
    snapshot = await get_analytics_snapshot(sqlite_path, window_days=window_days)
    return format_analytics(snapshot)

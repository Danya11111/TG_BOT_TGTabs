from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.bot.anti_spam import GroupAntiSpam
from app.bot.telegram_handlers import HandlerBundle
from app.config import get_settings
from app.db import ensure_db, fetch_all_articles
from app.kb.kb_loader import load_seed_to_db
from app.logging_setup import setup_logging
from app.observability.unknown_questions_logger import UnknownQuestionsLogger
from app.search.search_engine import SearchEngine

log = logging.getLogger(__name__)


async def bootstrap() -> tuple[Bot, Dispatcher]:
    load_dotenv()
    settings = get_settings()
    setup_logging(settings.log_level)

    await ensure_db(settings.sqlite_path)

    seed_path = Path("data/kb_seed.json")
    if seed_path.exists():
        loaded = await load_seed_to_db(settings.sqlite_path, seed_path.as_posix())
        log.info("Loaded seed KB articles: %s", loaded)

    rows = await fetch_all_articles(settings.sqlite_path)
    if not rows:
        log.warning("KB is empty. Add seed or run parser scripts before bot start.")

    search_engine = SearchEngine(rows)
    anti_spam = GroupAntiSpam(settings.sqlite_path, settings.group_antispam_ttl_sec)
    unknown_logger = UnknownQuestionsLogger(settings.sqlite_path)

    bundle = HandlerBundle(
        sqlite_path=settings.sqlite_path,
        bot_username=settings.bot_username,
        search_engine=search_engine,
        anti_spam=anti_spam,
        unknown_logger=unknown_logger,
        min_confidence=settings.min_confidence,
        ambiguity_delta=settings.ambiguity_delta,
        owner_ids=settings.owner_ids_set,
    )

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Set it in .env before running the bot.")
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    dp.include_router(bundle.create_router())
    return bot, dp


async def run() -> None:
    bot, dp = await bootstrap()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())

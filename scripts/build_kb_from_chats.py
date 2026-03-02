from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.env.settings import get_settings
from tgtaps_support_bot.infrastructure.persistence.sqlite_gateway import ensure_db, upsert_articles
from tgtaps_support_bot.infrastructure.parsers.chat_parser import build_qa_from_exports


async def main() -> None:
    parser = argparse.ArgumentParser(description="Build KB entries from Telegram exported chats.")
    parser.add_argument("--export-dir", default="data/raw_exports", help="Directory with messages*.html files")
    args = parser.parse_args()

    load_dotenv()
    settings = get_settings()
    await ensure_db(settings.sqlite_path)

    export_dir = Path(args.export_dir).resolve()
    items = build_qa_from_exports(export_dir.as_posix(), settings.support_usernames_set)
    count = await upsert_articles(settings.sqlite_path, items)
    print(f"Imported {count} chat-based KB entries from {export_dir}")


if __name__ == "__main__":
    asyncio.run(main())

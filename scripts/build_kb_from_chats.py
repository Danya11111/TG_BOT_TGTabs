from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from app.config import get_settings
from app.db import ensure_db, upsert_articles
from app.parsers.chat_parser import build_qa_from_exports


async def main() -> None:
    parser = argparse.ArgumentParser(description="Build KB entries from Telegram exported chats.")
    parser.add_argument("--export-dir", default=".", help="Directory with messages*.html files")
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

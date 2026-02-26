from __future__ import annotations

import argparse
import asyncio

from dotenv import load_dotenv

from app.config import get_settings
from app.db import ensure_db, upsert_articles
from app.parsers.doc_parser import crawl_docs_to_articles


async def main() -> None:
    parser = argparse.ArgumentParser(description="Build KB entries from docs website.")
    parser.add_argument("--start-url", default=None, help="Docs start URL")
    args = parser.parse_args()

    load_dotenv()
    settings = get_settings()
    await ensure_db(settings.sqlite_path)

    start_urls = [args.start_url] if args.start_url else [
        settings.docs_base_url,
        "https://tgtaps.gitbook.io/tgtaps-docs",
        "https://docs.tgtaps.com/tgtaps-docs",
    ]
    total = 0
    used = []
    for url in [u for u in start_urls if u]:
        items = crawl_docs_to_articles(url, max_pages=settings.docs_max_pages, max_depth=settings.docs_max_depth)
        if not items:
            continue
        count = await upsert_articles(settings.sqlite_path, items)
        total += count
        used.append(url)
    if used:
        print(f"Imported {total} docs-based KB entries from: {', '.join(used)}")
    else:
        print("Imported 0 docs-based KB entries (docs URL not reachable in current environment)")


if __name__ == "__main__":
    asyncio.run(main())

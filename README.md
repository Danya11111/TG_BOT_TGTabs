# TgTaps Support Bot (Production-Ready, Rule-Based)

Telegram support bot for TgTaps with no runtime neural networks.

## What it does

- Private chats:
  - accepts user question
  - finds best KB answer
  - sends structured response: summary, step-by-step guide, docs links, video links, similar questions
- Groups:
  - sends short answer
  - invites user to continue in DM for full answer
  - prevents duplicate spam answers for same question
- KB pipeline:
  - imports from Telegram chat exports (`messages*.html`)
  - imports from documentation pages (crawler)
  - supports tags, aliases, categories, versioned answers
- Operations:
  - logs unknown questions for KB growth
  - stores last answer per user to preserve context

## Architecture

- `app/parsers` - chat/docs ingestion into KB articles
- `app/kb` - seed loader
- `app/search` - exact + alias + keyword + fuzzy ranking
- `app/bot` - Telegram handlers and anti-spam
- `app/formatters` - answer templates
- `app/observability` - unknown question logger
- `app/db.py` - schema and data access (SQLite)

## Setup

1. Create virtual env and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure env:

```bash
copy .env.example .env
```

Fill `BOT_TOKEN` and `BOT_USERNAME`.

3. Build KB from your data:

```bash
python -m scripts.build_kb_from_chats --export-dir .
python -m scripts.build_kb_from_docs --start-url https://docs.tgtaps.com/tgtaps-docs
```

4. Run bot:

```bash
python -m app.main
```

## Notes

- Current anti-spam uses SQLite TTL dedup table.
- For horizontal scaling replace `GroupAntiSpam` storage with Redis.
- Unknown questions are stored in `kb_unknown_questions` table.

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
  - owner-only analytics command: `/analitics` (alias `/analytics`)

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
Also set `OWNER_IDS` with your Telegram user id.

3. Build KB from your data:

```bash
python -m scripts.build_kb_from_chats --export-dir .
python -m scripts.build_kb_from_docs --start-url https://docs.tgtaps.com/tgtaps-docs
```

4. Run bot:

```bash
python -m app.main
```

## Docker

- Local run:

```bash
docker compose up --build
```

- Local CI-like cycle (build + tests + run):

```bash
docker compose -f docker-compose.local.yml up --build bot-test
docker compose -f docker-compose.local.yml up --build -d bot
```

- Dev mode (mounted sources):

```bash
docker compose -f docker-compose.dev.yml up --build
```

## CI/CD

- CI workflow: `.github/workflows/ci.yml`
  - Ruff lint
  - Python compile check
  - Pytest
  - Docker build smoke
- CD workflow: `.github/workflows/cd.yml`
  - Build and push image to `ghcr.io/<owner>/<repo>`
  - Optional VPS deploy via SSH when secrets are configured:
    - `DEPLOY_HOST`
    - `DEPLOY_USER`
    - `DEPLOY_SSH_KEY`

## Owner Analytics Command

Send `/analitics` in DM to the bot (owner only), report includes:

1. Top 10 requests
2. Total requests
3. Latest 10 requests
4. Quality section: unknown rate, private/group split, top categories, action hints

## Notes

- Current anti-spam uses SQLite TTL dedup table.
- For horizontal scaling replace `GroupAntiSpam` storage with Redis.
- Unknown questions are stored in `kb_unknown_questions` table.

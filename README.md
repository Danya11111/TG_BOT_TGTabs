# TgTaps Support Bot

Production-ready Telegram support bot with strict layered architecture and rule-based KB search.

## Architecture Overview

Project is organized into explicit layers:

- `src/tgtaps_support_bot/domain` - entities, value objects, domain search logic.
- `src/tgtaps_support_bot/application` - use-cases and orchestration contracts.
- `src/tgtaps_support_bot/infrastructure` - DB gateway, parsers, logging, anti-spam adapters.
- `src/tgtaps_support_bot/presentation` - Telegram handlers/keyboards and output formatters.
- `config` - env, docker, and CI workflow copies.
- `data` - seed, generated artifacts, and raw exports separated by lifecycle.
- `archive/candidates_for_review` - archived artifacts kept for audit/review.

Legacy `app/*` modules are kept as compatibility shims to avoid breaking existing entrypoints/imports.

## Repository Map

```text
.
├─ src/tgtaps_support_bot/
│  ├─ domain/
│  ├─ application/
│  ├─ infrastructure/
│  └─ presentation/
├─ config/
│  ├─ env/
│  ├─ docker/
│  └─ ci/workflows/
├─ scripts/
├─ tests/
│  ├─ unit/domain/
│  ├─ unit/presentation/
│  └─ integration/
├─ data/
│  ├─ seed/
│  ├─ generated/
│  └─ raw_exports/
├─ docs/
│  ├─ architecture/
│  └─ reports/assets/
└─ archive/candidates_for_review/
```

## Quick Start

1. Create virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create local environment file:

```bash
copy config\env\.env.example .env
```

3. Build KB from exports/docs:

```bash
python -m scripts.build_kb_from_chats --export-dir data/raw_exports
python -m scripts.build_kb_from_docs --start-url https://tgtaps.gitbook.io/tgtaps-docs
```

4. Run bot:

```bash
python -m app.main
```

## Docker Commands

- Local run:

```bash
docker compose -f config/docker/docker-compose.yml up --build
```

- Local CI-like cycle:

```bash
docker compose -f config/docker/docker-compose.local.yml up --build bot-test
docker compose -f config/docker/docker-compose.local.yml up --build -d bot
```

- Dev mode:

```bash
docker compose -f config/docker/docker-compose.dev.yml up --build
```

## Commands for Data and Reports

- Generate group QA analytics artifacts:

```bash
python -m scripts.generate_group_qa_report --export-dir data/raw_exports --out-dir data/generated
```

## CI/CD

- Active workflows: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`
- Mirror copies: `config/ci/workflows/ci.yml`, `config/ci/workflows/cd.yml`

## Owner Analytics

Use `/analitics` or `/analytics` in bot DM (owner only). Report includes:

1. Top 10 requests
2. Request volume
3. Latest 10 requests
4. Quality section (unknown rate, private/group split, top categories)
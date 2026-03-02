# Technical Debt Register

## High Priority

- Keep dual module trees (`app/*` shims + `src/tgtaps_support_bot/*`) only as temporary migration phase.
  - Risk: duplicated navigation surface and accidental edits in shim files.
  - Action: remove `app/*` shims after one stable release cycle.

- `application` layer is introduced, but only part of orchestration is extracted from Telegram handlers.
  - Risk: business orchestration remains coupled to transport layer.
  - Action: continue extracting message flow logic into dedicated use-case services with transport-agnostic DTOs.

## Medium Priority

- CI/CD workflows are duplicated in `.github/workflows` and `config/ci/workflows`.
  - Risk: configuration drift.
  - Action: keep `.github/workflows` as source of truth and add automated sync check.

- Docker setup still launches through legacy compatibility entrypoint (`python -m app.main`).
  - Risk: hides migration completion status.
  - Action: switch runtime command to `python -m tgtaps_support_bot.presentation.telegram.bootstrap` after shim removal.

## Low Priority

- No integration tests for end-to-end Telegram update handling.
  - Risk: regressions in callback/message routing can pass unit tests.
  - Action: add integration tests with mocked aiogram dispatcher and sqlite fixture.

- Data archive and generated outputs are separated, but there is no retention policy.
  - Risk: unbounded growth of archived/generated artifacts.
  - Action: add retention rules and optional cleanup script in `scripts/`.

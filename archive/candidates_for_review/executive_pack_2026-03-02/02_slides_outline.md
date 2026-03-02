# TgTaps — Slides Outline (PowerPoint-ready)

## Slide 1 — Transforming Support at Scale
- **Основной тезис:** Поддержка превращена из реактивной функции в управляемую платформу.
- **График/диаграмма:** Maturity ladder (Reactive -> Structured -> Scalable).
- **Вывод:** Заложен фундамент масштабирования без линейного роста headcount.

## Slide 2 — Why Change Was Needed
- **Основной тезис:** Ручная поддержка не масштабируется при росте обращений.
- **График/диаграмма:** Pareto тем запросов (на базе `group_chat_analytics.md`).
- **Вывод:** Автоматизация топ-категорий дает максимальный бизнес-эффект.

## Slide 3 — AS-IS: Core Pain Points
- **Основной тезис:** Фрагментированные знания + отсутствие полного контура метрик.
- **График/диаграмма:** Current-state user journey (chat -> wait -> manual reply -> repeat).
- **Вывод:** Без системного цикла улучшения качество поддержки нестабильно.

## Slide 4 — Solution Architecture (TO-BE)
- **Основной тезис:** Построен end-to-end контур: ingestion -> KB -> retrieval -> observability.
- **График/диаграмма:** Архитектурная схема компонентов бота и БД.
- **Вывод:** Управление знаниями и качеством стало централизованным.

## Slide 5 — UX Improvements
- **Основной тезис:** Ответы стали структурированными и action-oriented.
- **График/диаграмма:** Flow: group short answer -> DM full answer -> disambiguation.
- **Вывод:** Пользователь быстрее доходит до решения, меньше фрустрации.

## Slide 6 — Reliability & Engineering Maturity
- **Основной тезис:** Укреплен операционный контур стабильности.
- **График/диаграмма:** CI/CD pipeline (lint, tests, docker build, deploy).
- **Вывод:** Снижен риск регрессий и ручных ошибок релиза.

## Slide 7 — Factual Baseline
- **Основной тезис:** Уже есть валидный количественный baseline.
- **График/диаграмма:** KPI cards:
  - 4,428 сообщений [фактическая]
  - 1,103 вопросов [фактическая]
  - 595 Q/A пар [фактическая]
  - 53.9% вопросов с ответом [фактическая]
- **Вывод:** Решения по приоритетам можно принимать data-driven.

## Slide 8 — Quantified Business Impact (Modeled)
- **Основной тезис:** Потенциал заметной экономии и ускорения поддержки.
- **График/диаграмма:** Waterfall "ручные часы до/после", scenario bars (conservative/base/aggressive).
- **Вывод:** Потенциал: -20-35% нагрузки, +5-12 п.п. конверсии в целевые действия [оценочные].

## Slide 9 — Risks and Mitigation
- **Основной тезис:** Риски прозрачны и управляемы.
- **График/диаграмма:** Risk heatmap (technical/product/organizational) + mitigation owners.
- **Вывод:** Ключевые риски покрываются roadmap-мероприятиями.

## Slide 10 — Roadmap (0-180 Days)
- **Основной тезис:** План развития разбит на три управляемых этапа.
- **График/диаграмма:** Timeline:
  - 0-30: stabilize & instrument
  - 30-90: scale & optimize
  - 90-180: productize
- **Вывод:** Есть реалистичный путь от стабильности к масштабируемости.

## Slide 11 — KPI Cockpit
- **Основной тезис:** Успех определяется конкретными KPI с целями.
- **График/диаграмма:** Таблица target vs baseline:
  - containment rate
  - unknown rate
  - time-to-first-answer
  - repeat question rate
- **Вывод:** Продукт поддержки становится управляемым как бизнес-функция.

## Slide 12 — Decision Ask
- **Основной тезис:** Инициатива готова к масштабированию.
- **График/диаграмма:** Decision tree + ROI hypothesis.
- **Вывод:** Рекомендовано утвердить фазу scale и KPI governance на 90 дней.

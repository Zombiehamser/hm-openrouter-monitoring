# hm-openrouter-monitoring

English version: [README.md](README.md)

[![Tests](https://github.com/Zombiehamser/hm-openrouter-monitoring/actions/workflows/test.yml/badge.svg)](https://github.com/Zombiehamser/hm-openrouter-monitoring/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Набор скриптов и skill для Hermes Agent, предназначенный для мониторинга расходов OpenRouter.

Проект выносит рутинный мониторинг OpenRouter за пределы LLM-слоя, чтобы обычные cron-задачи не тратили токены.

## Зачем это нужно

Во многих конфигурациях Hermes дорогостоящая часть — не сам вызов OpenRouter API, а то, что даже простые задачи мониторинга могут без необходимости идти через слой агента.

В результате даже обычные периодические проверки начинают расходовать токены, особенно при длинных сессиях и больших промптах.

Проект разделяет мониторинг на два уровня:

- **Watchdog** — частый, чистый Python, без агента, без LLM.
- **Analyzer** — объяснение через агента только при наличии реальной аномалии.

Арифметика и пороги остаются вне модели, а человекочитаемые summary появляются только тогда, когда действительно есть что объяснять.

## Как это работает

Watchdog ходит в OpenRouter по расписанию, вычисляет детерминированный суточный расход по дельте `total_usage` и записывает небольшой набор state-файлов.

Если пороги превышены, он создаёт машиночитаемый payload аномалии.

Отдельный analyzer-скрипт или Hermes-задача затем может прочитать эти файлы и попросить агента коротко объяснить, что произошло и нужно ли действие оператора.

На практике watchdog:

- получает текущий usage и balance из OpenRouter;
- сравнивает `total_usage` с предыдущим checkpoint;
- вычисляет `usage_daily_computed` как max-clamped delta;
- записывает `status.json`, `daily_state.json` и `anomaly.json`;
- завершает работу тихо, если аномалий нет.

## Архитектура

```text
OpenRouter API
     |
     v
openrouter_watchdog.py  --no-agent-->  status.json / daily_state.json / anomaly.json
                                                   |
                                                   v
                             openrouter_anomaly_analyzer.py --> compact JSON
                                                   |
                                                   v
                                 Hermes agent formats alert only on anomaly
```

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — рекомендуемый пакетный менеджер
- Hermes Agent установлен и настроен
- OpenRouter API key с включённым billing

## Быстрый старт

Клонируй репозиторий и создай виртуальное окружение:

```bash
git clone https://github.com/Zombiehamser/hm-openrouter-monitoring.git
cd hm-openrouter-monitoring
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Дальше открой нужную инструкцию:

- Ручная установка: [docs/installation.ru.md](docs/installation.ru.md)
- Адаптация под свою инфраструктуру: [docs/customization.ru.md](docs/customization.ru.md)
- Готовые промпты для Hermes: [docs/hermes-prompt.ru.md](docs/hermes-prompt.ru.md)

## Опциональные возможности

Некоторые части проекта являются опциональными и должны явно подтверждаться во время установки.

К ним относятся:

- конвертация в локальную валюту в отчётах, например в RUB;
- утренние summary-отчёты, например `openrouter_daily_brief.py`;
- пользовательские пороги аномалий;
- пользовательские расписания cron и каналы доставки.

Если проект устанавливает Hermes, он должен сначала спросить владельца, какие опциональные возможности действительно нужны.

## Структура репозитория

```text
.
├── README.md
├── README.ru.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── scripts/
│   ├── __init__.py
│   ├── openrouter_watchdog.py
│   ├── openrouter_anomaly_analyzer.py
│   └── openrouter_daily_brief.py
├── skills/
│   └── devops/
│       └── openrouter-monitoring/
│           ├── SKILL.md
│           └── SKILL.ru.md
├── examples/
│   ├── cron-jobs.json
│   ├── status.sample.json
│   ├── daily_state.sample.json
│   └── anomaly.sample.json
├── tests/
│   └── test_watchdog.py
└── docs/
    ├── installation.md
    ├── installation.ru.md
    ├── customization.md
    ├── customization.ru.md
    ├── hermes-prompt.md
    └── hermes-prompt.ru.md
```

## Development

Запусти тесты локально:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt pytest
uv run pytest
```

## Design notes

- Рутинный polling остаётся вне агента.
- Арифметика остаётся вне LLM.
- `usage_daily` от провайдера рассматривается только как fallback.
- Минимальный структурированный контекст лучше полной истории для анализа аномалий.
- Опциональные возможности должны подтверждаться во время установки, а не включаться молча.

## License

MIT.
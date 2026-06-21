# Customization

English version: [customization.md](customization.md)

Этот документ объясняет, что именно нужно менять при установке `hm-openrouter-monitoring` в другую инфраструктуру.

## Что нужно настроить обязательно

Для каждой установки нужно проверить следующие вещи:

- OpenRouter API key
- локальную директорию скриптов Hermes
- директорию skill Hermes
- state-директорию watchdog
- cron-расписания
- канал доставки отчётов и алертов

## Пути инфраструктуры

В репозитории используются примерные пути:

- `/opt/hermes/local-scripts`
- `/opt/data/openrouter-watchdog`
- `/opt/data/openrouter-watchdog/state`

Это примеры, а не обязательные пути.

Если в вашей установке Hermes используются другие директории, нужно изменить:

- команды копирования скриптов;
- команды установки skill;
- переменные окружения;
- пути к скриптам в cron-задачах.

## Переменные окружения

Основные переменные:

- `OPENROUTER_API_KEY`
- `OPENROUTER_WATCHDOG_BASE_DIR`
- `OPENROUTER_WATCHDOG_STATE_DIR`
- `OPENROUTER_WATCHDOG_STATE_FILE`

Перед автоматическим применением Hermes должен подтвердить итоговые значения с владельцем.

## Cron-расписания

Примеры расписаний в этом репозитории — только примеры.

Для новой установки нужно решить:

- как часто запускать watchdog;
- запускать ли anomaly analyzer по расписанию или условно;
- нужен ли вообще daily brief.

## Опциональные возможности

Следующие возможности опциональны и не должны включаться молча:

- конвертация в локальную валюту, включая RUB;
- `openrouter_daily_brief.py`;
- пользовательские пороги аномалий;
- доставка в Telegram или другой канал;
- дополнительные эвристики аномалий, завязанные на локальные привычки или рабочие часы.

Если настройка выполняется через Hermes, он должен спросить владельца, какие опциональные возможности нужно включить.

## Что лучше не менять

Обычно без необходимости не нужно менять следующие принципы:

- двухслойную архитектуру;
- watchdog без агента;
- analyzer только при наличии anomaly data;
- детерминированный суточный расход по дельтам `total_usage`;
- использование `usage_daily` только как fallback.

## Рекомендуемый checklist

Перед применением конфигурации проверь:

- корректны ли пути для локального хоста;
- уже задан ли OpenRouter API key или будет ли он добавлен безопасно;
- есть ли права на запись в state-директорию;
- были ли явно подтверждены опциональные возможности;
- не конфликтуют ли cron-расписания с существующими задачами;
- правильно ли указан канал доставки.

## Замечание по безопасной публикации

Если эти скрипты адаптируются из внутреннего деплоя, не публикуйте:

- реальные API keys;
- пользовательские home-paths;
- приватные hostnames;
- внутренние usernames;
- инфраструктурно-специфичные расписания, если они не помечены как examples.
## Язык и режимы вывода

All CLI scripts default to английский язык, только USD values only.

### Optional flags

| Flag | Scripts | Effect |
|---|---|---|
| `--lang ru` | analyzer, brief | Russian text with emoji, for Telegram-style delivery |
| `--show-rub` | analyzer, brief | Fetch USD/RUB rate from er-api.com and add RUB equivalents |
| `--verbose` (`-v`) | analyzer | Always print status message; disable [SILENT] mode |

### [SILENT] behavior

The anomaly analyzer prints `[SILENT]` when no anomaly file exists.
In Hermes cron, a task whose script prints exactly `[SILENT]` suppresses
delivery — nothing is sent to the user. Use `--verbose` for interactive use.

### Enabling RUB and Russian

These are **opt-in only**. Example commands:

```bash
# English, USD only (default — подходит для всех платформ)
python3 /path/to/openrouter_anomaly_analyzer.py
python3 /path/to/openrouter_daily_brief.py

# Russian with RUB (Telegram-oriented)
python3 /path/to/openrouter_anomaly_analyzer.py --lang ru --show-rub
python3 /path/to/openrouter_daily_brief.py --lang ru --show-rub
```

No environment variables are required for these flags. The project works fully
without them. Other users can adapt the currency flag to their needs (EUR, GBP,
JPY, etc.) by wrapping the script or modifying the exchange-rate URL.

### Environment variables for thresholds

The watchdog now supports these additional environment variables:

- `OPENROUTER_DAILY_THRESHOLD_USD` — daily spend threshold (default: 5.0)
- `OPENROUTER_BALANCE_THRESHOLD_USD` — remaining balance threshold (default: 3.0)
- `OPENROUTER_TOTAL_USAGE_THRESHOLD_USD` — total usage threshold (default: 50.0)
- `OPENROUTER_DAILY_SPIKE_PCT` — daily growth spike percentage (default: 300)
- `OPENROUTER_SAVE_RAW_RESPONSES` — set to "true" to save raw API responses for debugging

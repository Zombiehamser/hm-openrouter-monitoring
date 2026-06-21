---
name: openrouter-monitoring
description: "Двухслойный мониторинг OpenRouter для Hermes Agent: частый watchdog без агента, анализ аномалий только при необходимости."
category: devops
---

# OpenRouter Monitoring

English version: [SKILL.md](SKILL.md)

## Purpose

Мониторить баланс и расход OpenRouter, оставляя рутинные проверки вне LLM-слоя.

## Architecture

Стек состоит из трёх компонентов (в порядке частоты):

**Layer 1: Watchdog (`openrouter_watchdog.py`)**
- script-only, no_agent=true, ноль внешних зависимостей
- частое расписание (напр. каждый час)
- запрашивает /credits и /auth/key через OpenAI API
- пишет status.json, daily_state.json, anomaly.json, usage_history.jsonl, heartbeat.epoch
- обнаруживает 4 типа аномалий

**Layer 2: Analyzer (`openrouter_anomaly_analyzer.py`)**
- читает anomaly.json и формирует структурированный отчёт
- по умолчанию: [SILENT] если аномалий нет
- --verbose / --lang ru / --show-rub — опциональные флаги

**Layer 3: Daily Brief (`openrouter_daily_brief.py`)**
- опциональный утренний отчёт, no_agent=true
- --lang ru / --show-rub — опционально

## SILENT режим и cron

Анализатор выводит [SILENT] и завершается с кодом 0, когда аномалий нет.
В Hermes cron задача, чьёт скрипт вывел [SILENT], не доставляется — ничего не попадает пользователю.
Используйте --verbose для интерактивного режима.

## Language and currency modes

По умолчанию: английский, только USD.

Флаги локализации (опционально):
- --lang ru: русский язык с эмодзи
- --show-rub: конвертация в рубли

[Остальной текст соответствует английской версии выше]

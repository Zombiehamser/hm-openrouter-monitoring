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

```text
Layer 1: Watchdog
- script-only
- no_agent=true
- частый запуск
- пишет status.json, daily_state.json, anomaly.json
- завершается тихо, если аномалий нет

Layer 2: Analyzer
- Hermes-задача или тонкий скрипт
- читает anomaly.json
- запускается только при наличии anomaly data
- формирует короткий summary для оператора
```

## Expected files

Стек мониторинга предполагает использование следующих файлов:

- `status.json`
- `daily_state.json`
- `anomaly.json`
- `usage_history.jsonl`
- `heartbeat.epoch`

## Core rules

- Не использовать LLM в слое watchdog.
- Использовать детерминированный суточный расход на основе дельт `total_usage`.
- Рассматривать `usage_daily` от провайдера только как fallback-данные.
- Держать anomaly detection детерминированным.
- Использовать агента только для короткого человекочитаемого summary при наличии anomaly data.

## Configuration notes

Инфраструктурно-специфичные значения должны задаваться вне skill:

- пути файловой системы;
- cron-расписания;
- каналы доставки;
- опциональные возможности, например конвертация в локальную валюту.

Эти вещи должны настраиваться через локальную конфигурацию, документацию или явное подтверждение владельца во время установки.

## Safe changes

Обычно безопасно настраивать:

- значения порогов;
- расписания;
- способ доставки;
- опциональные отчёты, например daily brief.

## Avoid changing

Обычно без необходимости не стоит менять:

- watchdog без агента;
- analyzer, запускаемый по anomaly data;
- детерминированный расчёт суточного расхода;
- разделение между сбором state и генерацией LLM-summary.
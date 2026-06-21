---
name: openrouter-monitoring
description: "Two-layer OpenRouter monitoring for Hermes Agent: frequent watchdog without agent, anomaly analysis only when needed."
category: devops
---

# OpenRouter Monitoring

Русская версия: [SKILL.ru.md](SKILL.ru.md)

## Purpose

Monitor OpenRouter balance and spending while keeping routine checks outside the LLM layer.

## Architecture

The stack has three components, listed in order of frequency:

**Layer 1: Watchdog (`openrouter_watchdog.py`)**
- script-only, no_agent=true, zero external dependencies
- frequent schedule (e.g. every hour)
- fetches /credits and /auth/key from OpenRouter API
- writes status.json, daily_state.json, anomaly.json, usage_history.jsonl, heartbeat.epoch
- detects 4 anomaly types: daily_usage_high, balance_low, total_usage_high, daily_usage_spike

**Layer 2: Analyzer (`openrouter_anomaly_analyzer.py`)**
- reads anomaly.json and produces a structured human-readable report
- default mode: [SILENT] when no anomaly exists (suppresses cron delivery)
- --verbose: always print status message
- --lang ru: Russian text with emoji (Telegram-friendly)
- --show-rub: include USD/RUB conversion

**Layer 3: Daily Brief (`openrouter_daily_brief.py`)**
- optional morning summary, no_agent=true
- fetches current balance, total usage, and 24h spend from OpenRouter
- --lang ru / --show-rub for localization (optional, opt-in only)

## Expected files

The monitoring stack uses these files in the state directory:

- `status.json`
- `daily_state.json`
- `anomaly.json`
- `usage_history.jsonl`
- `heartbeat.epoch`

## Core rules

- Do not use the LLM in the watchdog layer.
- Use deterministic daily spend based on `total_usage` deltas.
- Treat provider-reported `usage_daily` as fallback data only.
- Keep anomaly detection deterministic.
- Use the agent only for short human-readable summaries when anomaly data exists.

## Language and currency modes

**Default (English, USD only):** all scripts print clean English text suitable for logs, CI, email, CLI, and any platform.

**“--lang ru” (Russian):** human-oriented output with emoji, designed for Telegram-style delivery.

**“--show-rub” (RUB conversion):** fetches USD/RUB exchange rate from er-api.com and adds RUB equivalents.

Both flags are optional. The project works fully without them.

## Этот критически для корректной работы с cron

The analyzer prints [SILENT] and exits with code 0 when no anomaly file exists.
This is the default. In Hermes cron, a task whose script prints [SILENT] will
have its delivery suppressed — nothing reaches the user. This is by design.
Use --verbose for interactive or debugging use.

## Configuration notes

Infrastructure-specific values should be configured outside the skill:

- filesystem paths;
- cron schedules;
- delivery targets;
- optional features such as local currency conversion or Russian language.

These should be handled through local configuration, docs, or owner confirmation during setup.

## Safe changes

The following parts are usually safe to customize:

- threshold values (via OPENROUTER_* env vars);
- schedules;
- delivery method;
- optional reports such as daily brief;
- language and currency flags.

## Avoid changing

The following design should normally stay unchanged:

- watchdog without agent;
- analyzer triggered by anomaly data;
- deterministic daily spend calculation;
- separation between state collection and LLM summary generation.

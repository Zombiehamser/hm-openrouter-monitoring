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

```text
Layer 1: Watchdog
- script-only
- no_agent=true
- frequent schedule
- writes status.json, daily_state.json, anomaly.json
- exits quietly when there is no anomaly

Layer 2: Analyzer
- Hermes task or thin script
- reads anomaly.json
- runs only when anomaly data exists
- produces a short operator-facing summary
```

## Expected files

The monitoring stack is expected to use these files:

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

## Configuration notes

Infrastructure-specific values should be configured outside the skill:

- filesystem paths;
- cron schedules;
- delivery targets;
- optional features such as local currency conversion.

These should be handled through local configuration, docs, or owner confirmation during setup.

## Safe changes

The following parts are usually safe to customize:

- threshold values;
- schedules;
- delivery method;
- optional reports such as daily brief.

## Avoid changing

The following design should normally stay unchanged:

- watchdog without agent;
- analyzer triggered by anomaly data;
- deterministic daily spend calculation;
- separation between state collection and LLM summary generation.
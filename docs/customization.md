# Customization

Русская версия: [customization.ru.md](customization.ru.md)

This document explains what should be changed when installing `hm-openrouter-monitoring` into a different infrastructure.

## What must be configured

The following items must be checked for every installation:

- OpenRouter API key
- local Hermes scripts directory
- Hermes skill directory
- watchdog state directory
- cron schedules
- delivery target for reports and alerts

## Infrastructure paths

The repository uses example paths such as:

- `/opt/hermes/local-scripts`
- `/opt/data/openrouter-watchdog`
- `/opt/data/openrouter-watchdog/state`

These are examples, not mandatory paths.

If your Hermes installation uses different directories, change:

- script copy commands;
- skill install commands;
- environment variables;
- cron job script paths.

## Environment variables

The main variables are:

- `OPENROUTER_API_KEY`
- `OPENROUTER_WATCHDOG_BASE_DIR`
- `OPENROUTER_WATCHDOG_STATE_DIR`
- `OPENROUTER_WATCHDOG_STATE_FILE`

Before applying any setup automatically, Hermes should confirm the final values with the owner.

## Cron schedules

The default examples in this repository are only examples.

A new installation should decide:

- how often the watchdog runs;
- whether the anomaly analyzer runs on a schedule or conditionally;
- whether the daily brief is enabled at all.

## Optional features

The following features are optional and should not be enabled silently:

- local currency conversion, including RUB;
- `openrouter_daily_brief.py`;
- custom anomaly thresholds;
- delivery to Telegram or another destination;
- extra anomaly heuristics based on local habits or working hours.

If Hermes is used for setup, it should ask the owner which optional features should be enabled.

## What can stay unchanged

The following design should normally stay unchanged:

- two-layer architecture;
- watchdog without agent;
- analyzer only when anomaly data exists;
- deterministic daily spend based on `total_usage` deltas;
- `usage_daily` treated as fallback only.

## Recommended review checklist

Before applying configuration changes, verify:

- paths are correct for the local host;
- the OpenRouter API key is already present or will be added safely;
- the state directory is writable;
- optional features were explicitly approved;
- cron schedules do not conflict with existing jobs;
- delivery targets are correct.

## Safe publishing note

If you adapt these scripts from an internal deployment, do not publish:

- real API keys;
- user-specific home paths;
- private hostnames;
- internal usernames;
- infrastructure-specific schedules unless they are clearly marked as examples.
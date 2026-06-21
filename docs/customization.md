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
## Language and currency modes

All CLI scripts default to English output with USD values only.

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
# English, USD only (default — suitable for all platforms)
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

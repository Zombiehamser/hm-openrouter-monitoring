# Hermes setup prompts

Русская версия: [hermes-prompt.ru.md](hermes-prompt.ru.md)

This document contains example prompts for using Hermes to install and configure `hm-openrouter-monitoring`.

## Prompt 1: guided installation

Use this prompt when the repository is already cloned and you want Hermes to install it safely.

```text
Install hm-openrouter-monitoring from the current repository into this Hermes environment.

Before applying any changes, inspect the local filesystem and determine:
- the correct Hermes scripts directory;
- the correct Hermes skills directory;
- the correct state directory for watchdog files;
- whether OPENROUTER_API_KEY is already configured;
- whether there are existing OpenRouter-related cron jobs.

Ask me before enabling any optional features, including:
- local currency conversion such as RUB;
- daily brief reporting;
- Telegram delivery;
- custom thresholds;
- custom schedules.

Do not assume /opt paths unless they already exist and match the current system.

After inspection, show:
1. the paths you want to use;
2. the environment variables you want to set;
3. the cron jobs you want to create or update;
4. the exact files you want to copy.

Wait for my confirmation before changing anything.
```

## Prompt 2: adapt existing installation

Use this prompt when OpenRouter monitoring already exists and you want Hermes to align it with this repository.

```text
Audit the current Hermes environment and compare it with the hm-openrouter-monitoring repository.

Find the currently installed versions of:
- openrouter_watchdog.py
- openrouter_anomaly_analyzer.py
- openrouter_daily_brief.py
- any related skills or cron jobs

Then prepare a minimal adaptation plan.

Rules:
- do not break the existing working setup;
- preserve infrastructure-specific paths unless replacement is necessary;
- identify optional features separately from required changes;
- ask before enabling local currency conversion, daily brief reporting, or Telegram delivery;
- show diffs before writing files.

Output:
1. current state summary;
2. proposed changes;
3. files to update;
4. questions that require owner confirmation.
```

## Prompt 3: verification only

Use this prompt when you only want Hermes to validate the setup without changing anything.

```text
Inspect the current hm-openrouter-monitoring installation in this Hermes environment.

Check:
- script locations;
- skill locations;
- state directory;
- environment variables used by the scripts;
- existing cron jobs;
- whether the watchdog can write state files.

Do not modify anything.

Return:
1. detected paths;
2. detected environment variables;
3. detected cron jobs;
4. missing pieces;
5. optional features currently enabled.
```
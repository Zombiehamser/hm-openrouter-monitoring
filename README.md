# hm-openrouter-monitoring

Русская версия: [README.ru.md](README.ru.md)

[![Tests](https://github.com/Zombiehamser/hm-openrouter-monitoring/actions/workflows/test.yml/badge.svg)](https://github.com/Zombiehamser/hm-openrouter-monitoring/actions/workflows/test.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A set of scripts and a Hermes skill for monitoring OpenRouter spending in Hermes Agent environments.

The project keeps routine OpenRouter monitoring outside the LLM layer, so regular cron jobs can run without spending tokens.

## Why this exists

In many Hermes setups, the expensive part is not the OpenRouter API call itself, but the fact that even simple monitoring tasks may run through the agent layer without real need.

As a result, simple periodic checks can still consume tokens, especially during long sessions with large prompts.

This project separates monitoring into two layers:

- **Watchdog** — frequent, pure Python, no agent, no LLM.
- **Analyzer** — agent-assisted explanation only when a real anomaly is present.

Arithmetic and thresholds stay outside the model, while human-readable summaries appear only when there is actually something to explain.

## How it works

The watchdog talks to OpenRouter on a schedule, computes a deterministic daily spend from `total_usage` deltas, and writes a small set of state files.

If thresholds are exceeded, it emits a machine-readable anomaly payload.

A separate analyzer script or Hermes task can then read these files and ask the agent to summarise what happened and whether operator action is needed.

In practice, the watchdog:

- fetches current OpenRouter usage and balance;
- compares `total_usage` against the previous checkpoint;
- computes `usage_daily_computed` as a max-clamped delta;
- writes `status.json`, `daily_state.json`, and `anomaly.json`;
- exits quietly when no anomaly is detected.

## Architecture

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
- [uv](https://docs.astral.sh/uv/) — recommended package manager
- Hermes Agent installed and configured
- OpenRouter API key with billing enabled

## Quick start

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Zombiehamser/hm-openrouter-monitoring.git
cd hm-openrouter-monitoring
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Read the setup guide:

- Manual installation: [docs/installation.md](docs/installation.md)
- Infrastructure-specific customization: [docs/customization.md](docs/customization.md)
- Hermes setup prompts: [docs/hermes-prompt.md](docs/hermes-prompt.md)

## Optional features

Some parts of the project are optional and should be explicitly confirmed during setup.

These include:

- local currency conversion in reports, for example RUB;
- morning summary reports such as `openrouter_daily_brief.py`;
- custom anomaly thresholds;
- custom cron schedules and delivery targets.

If Hermes is used to install this project, it should ask the owner which optional features are needed before applying changes.

## Repository structure

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

## Language & Output Modes

All CLI scripts use English output by default.

### Anomaly analyzer (`openrouter_anomaly_analyzer.py`)

```bash
python3 scripts/openrouter_anomaly_analyzer.py                  # EN, [SILENT] if no anomaly
python3 scripts/openrouter_anomaly_analyzer.py --verbose         # EN, always print status
python3 scripts/openrouter_anomaly_analyzer.py --lang ru         # RU, with emoji
python3 scripts/openrouter_anomaly_analyzer.py --show-rub        # EN + RUB conversion
python3 scripts/openrouter_anomaly_analyzer.py --lang ru --show-rub  # RU + RUB
```

Default behavior (`[SILENT]`): when no anomaly exists, the script prints exactly
`[SILENT]` and exits. This suppresses Hermes cron delivery so nothing reaches
the user. Use `--verbose` to always get a human-readable status message.

### Daily brief (`openrouter_daily_brief.py`)

```bash
python3 scripts/openrouter_daily_brief.py                        # EN, USD only
python3 scripts/openrouter_daily_brief.py --show-rub             # EN + RUB conversion
python3 scripts/openrouter_daily_brief.py --lang ru              # RU, with emoji
```

### Mode notes

- **EN mode** (default): clean plain text suitable for logs, CI, email, CLI, and all platforms.
- **RU mode** (`--lang ru`): Russian text with emoji, designed for human-oriented channels such as Telegram.
- **RUB conversion** (`--show-rub`): fetches the current USD/RUB exchange rate from er-api.com and includes RUB equivalents.
- Both `--lang ru` and `--show-rub` are **optional**. They must be explicitly enabled — the project works fully without them.

## Development

Run tests locally:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt pytest
uv run pytest
```

## Design notes

- Routine polling stays outside the agent.
- Arithmetic stays outside the LLM.
- `usage_daily` from the provider is treated as a fallback.
- Minimal structured context beats full history for anomaly analysis.
- Optional features should be confirmed during installation, not silently enabled.

## License

MIT.
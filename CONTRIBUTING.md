# Contributing

Русская версия: [CONTRIBUTING.ru.md](CONTRIBUTING.ru.md)

Thank you for your interest in `hm-openrouter-monitoring`.

This repository contains a small OpenRouter monitoring stack for Hermes Agent environments. Contributions are welcome, but the project aims to stay compact, practical, and easy to audit.

## Before you start

Please read these files first:

- `README.md` or `README.ru.md`
- `docs/installation.md` or `docs/installation.ru.md`
- `docs/customization.md` or `docs/customization.ru.md`
- `docs/hermes-prompt.md` or `docs/hermes-prompt.ru.md`

## What kind of changes are useful

Useful contributions include:

- bug fixes in the monitoring scripts;
- tests for deterministic watchdog logic;
- documentation fixes and clarifications;
- safer installation and customization guidance;
- improvements to sample files and CI configuration.

Please avoid changes that make the project significantly more complex without a clear operational benefit.

## Development setup

This project uses Python 3.11+ and `uv`.

Create a virtual environment and install dependencies:

### Linux/macOS

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt pytest
```

### Windows PowerShell

```powershell
uv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt pytest
```

Run tests:

```bash
uv run pytest
```

## Repository conventions

Please keep the following rules in mind:

- keep the watchdog layer free from LLM calls;
- keep arithmetic and anomaly thresholds deterministic;
- do not hardcode private infrastructure details;
- keep optional features optional;
- keep documentation bilingual when changing public-facing docs.

If you update one of these files, update the paired version too:

- `README.md` and `README.ru.md`
- `CONTRIBUTING.md` and `CONTRIBUTING.ru.md`
- `CHANGELOG.md` and `CHANGELOG.ru.md`
- `docs/*.md` and `docs/*.ru.md`
- `SKILL.md` and `SKILL.ru.md`

## Commit messages

This repository uses simple Conventional Commits style where practical.

Examples:

- `feat: add watchdog balance threshold test`
- `fix: handle missing anomaly file gracefully`
- `docs: clarify Windows uv activation`
- `ci: disable uv cache for requirements-based workflow`

## Pull requests

When opening a pull request, please:

- describe what changed;
- explain why the change is needed;
- mention any documentation updates;
- mention whether tests were added or updated.

Small, focused pull requests are preferred over large mixed changes.

## Reporting bugs

When reporting a bug, include:

- your OS;
- Python version;
- how you installed the project;
- the command you ran;
- the actual error output;
- the expected behavior.

## Security and privacy

Do not include real API keys, private hostnames, internal usernames, or production state files in issues or pull requests.

## Tone and scope

The goal of this repository is not to be a universal monitoring framework.

The goal is to provide a small, auditable, practical OpenRouter monitoring stack that works well with Hermes-style environments.
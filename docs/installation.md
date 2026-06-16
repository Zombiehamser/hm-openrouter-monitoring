# Installation

Русская версия: [installation.ru.md](installation.ru.md)

This document describes how to install `hm-openrouter-monitoring` into an existing Hermes Agent environment.

## Requirements

- Python 3.11+
- Hermes Agent installed and configured
- OpenRouter API key with billing enabled
- Write access to the directories used by Hermes and the watchdog
- `uv` installed locally

## Clone the repository

```bash
git clone https://github.com/Zombiehamser/hm-openrouter-monitoring.git
cd hm-openrouter-monitoring
```

## Create a virtual environment

Create and activate a local virtual environment with `uv`:

```bash
uv venv
source .venv/bin/activate
```

Install dependencies:

```bash
uv pip install -r requirements.txt
```

If your environment does not use `uv`, you may use a regular Python virtual environment as a fallback.

## Copy scripts

Copy the scripts into the local Hermes scripts directory:

```bash
mkdir -p /opt/hermes/local-scripts
cp scripts/*.py /opt/hermes/local-scripts/
chmod +x /opt/hermes/local-scripts/*.py
```

## Install the skill

Copy the skill into the Hermes skills directory:

```bash
mkdir -p ~/.hermes/skills/devops/openrouter-monitoring
cp skills/devops/openrouter-monitoring/SKILL.md ~/.hermes/skills/devops/openrouter-monitoring/
```

## Create the state directory

Create the state directory used by the watchdog:

```bash
mkdir -p /opt/data/openrouter-watchdog/state
```

If needed, adjust ownership and permissions so Hermes can write there:

```bash
chown -R hermes:hermes /opt/data/openrouter-watchdog/
```

## Configure environment variables

Set the required environment variables:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
export OPENROUTER_WATCHDOG_BASE_DIR="/opt/data/openrouter-watchdog"
export OPENROUTER_WATCHDOG_STATE_DIR="/opt/data/openrouter-watchdog/state"
export OPENROUTER_WATCHDOG_STATE_FILE="/opt/data/openrouter-watchdog/state/daily_state.json"
```

## Verify the watchdog

Run the watchdog manually once:

```bash
python3 /opt/hermes/local-scripts/openrouter_watchdog.py
```

Then verify that the expected state files are created:

```bash
ls -la /opt/data/openrouter-watchdog/state/
```

Typical output:

```text
anomaly.json
daily_state.json
heartbeat.epoch
status.json
usage_history.jsonl
```

## Next step

After installation, read [customization.md](customization.md) to decide what should be changed for your infrastructure.

Then use [hermes-prompt.md](hermes-prompt.md) if you want Hermes to finish the setup.
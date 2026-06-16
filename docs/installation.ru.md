# Installation

English version: [installation.md](installation.md)

Этот документ описывает, как установить `hm-openrouter-monitoring` в уже существующее окружение Hermes Agent.

## Requirements

- Python 3.11+
- Hermes Agent установлен и настроен
- OpenRouter API key с включённым billing
- Права на запись в директории Hermes и watchdog
- Локально установлен `uv`

## Клонирование репозитория

```bash
git clone https://github.com/Zombiehamser/hm-openrouter-monitoring.git
cd hm-openrouter-monitoring
```

## Создание виртуального окружения

Создай и активируй локальное виртуальное окружение через `uv`:

```bash
uv venv
source .venv/bin/activate
```

Установи зависимости:

```bash
uv pip install -r requirements.txt
```

Если в твоём окружении `uv` не используется, в качестве fallback можно применить обычный Python virtual environment.

## Копирование скриптов

Скопируй скрипты в локальную директорию скриптов Hermes:

```bash
mkdir -p /opt/hermes/local-scripts
cp scripts/*.py /opt/hermes/local-scripts/
chmod +x /opt/hermes/local-scripts/*.py
```

## Установка skill

Скопируй skill в директорию skills Hermes:

```bash
mkdir -p ~/.hermes/skills/devops/openrouter-monitoring
cp skills/devops/openrouter-monitoring/SKILL.md ~/.hermes/skills/devops/openrouter-monitoring/
```

## Создание state-директории

Создай директорию, которую watchdog будет использовать для state-файлов:

```bash
mkdir -p /opt/data/openrouter-watchdog/state
```

Если нужно, выдай Hermes права на запись:

```bash
chown -R hermes:hermes /opt/data/openrouter-watchdog/
```

## Настройка переменных окружения

Задай обязательные переменные окружения:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
export OPENROUTER_WATCHDOG_BASE_DIR="/opt/data/openrouter-watchdog"
export OPENROUTER_WATCHDOG_STATE_DIR="/opt/data/openrouter-watchdog/state"
export OPENROUTER_WATCHDOG_STATE_FILE="/opt/data/openrouter-watchdog/state/daily_state.json"
```

## Проверка watchdog

Один раз запусти watchdog вручную:

```bash
python3 /opt/hermes/local-scripts/openrouter_watchdog.py
```

Потом проверь, что state-файлы появились:

```bash
ls -la /opt/data/openrouter-watchdog/state/
```

Типичный вывод:

```text
anomaly.json
daily_state.json
heartbeat.epoch
status.json
usage_history.jsonl
```

## Следующий шаг

После установки открой [customization.ru.md](customization.ru.md), чтобы понять, что нужно менять под свою инфраструктуру.

Затем используй [hermes-prompt.ru.md](hermes-prompt.ru.md), если хочешь поручить оставшуюся настройку Hermes.
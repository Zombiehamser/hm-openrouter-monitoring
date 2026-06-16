# Contributing

English version: [CONTRIBUTING.md](CONTRIBUTING.md)

Спасибо за интерес к `hm-openrouter-monitoring`.

Этот репозиторий содержит небольшой стек мониторинга OpenRouter для окружений Hermes Agent. Контрибьюции приветствуются, но проект должен оставаться компактным, практичным и удобным для аудита.

## Перед началом

Сначала прочитай эти файлы:

- `README.md` или `README.ru.md`
- `docs/installation.md` или `docs/installation.ru.md`
- `docs/customization.md` или `docs/customization.ru.md`
- `docs/hermes-prompt.md` или `docs/hermes-prompt.ru.md`

## Какие изменения полезны

Полезными считаются:

- исправления ошибок в monitoring-скриптах;
- тесты для детерминированной логики watchdog;
- исправления и уточнения документации;
- улучшения инструкций по установке и адаптации;
- улучшения sample-файлов и CI-конфигурации.

Пожалуйста, избегай изменений, которые заметно усложняют проект без понятной операционной пользы.

## Окружение для разработки

Проект использует Python 3.11+ и `uv`.

Создай виртуальное окружение и установи зависимости:

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

Запуск тестов:

```bash
uv run pytest
```

## Правила репозитория

Пожалуйста, придерживайся следующих правил:

- не добавляй вызовы LLM в слой watchdog;
- держи арифметику и пороги аномалий детерминированными;
- не хардкодь приватные инфраструктурные детали;
- оставляй опциональные возможности действительно опциональными;
- сохраняй двуязычность public-facing документации.

Если меняешь один из этих файлов, обновляй и парную версию:

- `README.md` и `README.ru.md`
- `CONTRIBUTING.md` и `CONTRIBUTING.ru.md`
- `CHANGELOG.md` и `CHANGELOG.ru.md`
- `docs/*.md` и `docs/*.ru.md`
- `SKILL.md` и `SKILL.ru.md`

## Сообщения коммитов

По возможности в репозитории используется простой стиль Conventional Commits.

Примеры:

- `feat: add watchdog balance threshold test`
- `fix: handle missing anomaly file gracefully`
- `docs: clarify Windows uv activation`
- `ci: disable uv cache for requirements-based workflow`

## Pull requests

При открытии pull request:

- опиши, что именно изменено;
- объясни, зачем нужно изменение;
- укажи, были ли обновлены документы;
- укажи, были ли добавлены или изменены тесты.

Предпочтение отдаётся небольшим и сфокусированным pull request, а не большим смешанным изменениям.

## Сообщения об ошибках

Если ты сообщаешь об ошибке, приложи:

- свою ОС;
- версию Python;
- способ установки проекта;
- команду, которую ты запускал;
- фактический текст ошибки;
- ожидаемое поведение.

## Безопасность и приватность

Не публикуй реальные API keys, приватные hostnames, внутренние usernames или production state-files в issue и pull request.

## Тон и границы проекта

Цель этого репозитория — не стать универсальным monitoring framework.

Цель — предоставить небольшой, понятный для аудита и практически полезный стек мониторинга OpenRouter, хорошо подходящий для окружений в стиле Hermes.
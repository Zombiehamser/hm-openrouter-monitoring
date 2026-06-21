# Changelog

English version: [CHANGELOG.md](CHANGELOG.md)

Все заметные изменения в проекте документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-06-21

### Добавлено

- Rolling 24h spend: daily brief теперь вычисляет расход за 24ч через дельту
  total_usage по временному окну, а не через /auth/key.usage_daily (календарный
  счётчик, сбрасывается в 00:00 UTC). Это соответствует метрике "Past 1 Day"
  в панели OpenRouter.
- Параметр usage_reference в report builders: usage_daily из /auth/key
  показывается как вторичная reference-строка при отличии от rolling window.
- Тесты для fallback при пустой истории.

### Изменено

- daily_brief main(): rolling history window теперь PRIMARY source of truth
  для 24h расхода. Fallback на usage_daily только при пустой истории.

### Исправлено

- Daily brief теперь использует rolling 24h дельту total_usage из истории
  как основной источник, вместо /auth/key.usage_daily (календарный счётчик,
  сбрасывается в 00:00 UTC). Это синхронизирует отчёт с метрикой "Past 1 Day"
  в панели OpenRouter.
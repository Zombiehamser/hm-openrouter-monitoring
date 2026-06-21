#!/usr/bin/env python3
"""OpenRouter Anomaly Analyzer — reads watchdog state and produces a report.

Default (alert-only, cron-friendly):
  - No anomaly detected → prints [SILENT] (suppresses cron delivery)
  - Anomaly detected     → prints full analytical report (delivered to Telegram/etc.)

Options:
  --verbose (-v)         Always print status, even when no anomaly.
  --show-rub             Include USD/RUB conversion in financial summary.
  --lang ru              Russian-language output with emoji formatting.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


# ── Paths ───────────────────────────────────────────────────────────
BASE_DIR = os.environ.get(
    "OPENROUTER_WATCHDOG_BASE_DIR",
    "/opt/data/openrouter-watchdog",
)
STATE_DIR = os.environ.get(
    "OPENROUTER_WATCHDOG_STATE_DIR",
    os.path.join(BASE_DIR, "state"),
)

# ── Helpers ─────────────────────────────────────────────────────────
def read_file(filename: str) -> str | None:
    path = os.path.join(STATE_DIR, filename)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read()


def read_json(filename: str) -> dict | list | None:
    content = read_file(filename)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def read_jsonl_tail(filename: str, n: int = 50) -> list[dict]:
    path = os.path.join(STATE_DIR, filename)
    if not os.path.isfile(path):
        return []
    records: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records[-n:]


def to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def fmt_usd(v: Any) -> str:
    return f"${to_float(v):.4f}"


ER_API_URL = "https://open.er-api.com/v6/latest/USD"


def get_usd_rub() -> float | None:
    """Fetch USD/RUB rate from er-api.com. Uses only stdlib."""
    try:
        with urllib.request.urlopen(ER_API_URL, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            rate = data.get("rates", {}).get("RUB")
            if rate:
                return float(rate)
    except Exception:
        pass
    return None


# ── Report builders ────────────────────────────────────────────────
def build_report_en(
    status: dict | None,
    history: list[dict],
    anomaly: dict,
    usd_rub: float | None,
) -> str:
    """Build analytical report in English (default)."""
    return _build_report(status, history, anomaly, usd_rub, lang="en")


def build_report_ru(
    status: dict | None,
    history: list[dict],
    anomaly: dict,
    usd_rub: float | None,
) -> str:
    """Build analytical report in Russian with emoji."""
    return _build_report(status, history, anomaly, usd_rub, lang="ru")


def _build_report(
    status: dict | None,
    history: list[dict],
    anomaly: dict,
    usd_rub: float | None,
    lang: str,
) -> str:
    """Build the full analytical report string."""
    anomalies = anomaly.get("anomalies", [])
    if not isinstance(anomalies, list):
        anomalies = []
    lines: list[str] = []
    is_ru = lang == "ru"

    # ── Header ───────────────────────────────────────────────────
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if is_ru:
        lines.append("=" * 55)
        lines.append("  OpenRouter Anomaly Analyzer — Аналитический отчёт")
        lines.append(f"  {now_str}")
        lines.append("=" * 55)
    else:
        lines.append("=" * 55)
        lines.append("  OpenRouter Anomaly Analyzer — Analytical Report")
        lines.append(f"  {now_str}")
        lines.append("=" * 55)
    lines.append("")

    # ── Financial summary ────────────────────────────────────────
    remaining_usd: float | None = None
    total_usage_val: float | None = None
    spend_24h_val = 0.0

    if status:
        bal = to_float(status.get("balance"))
        tu = to_float(status.get("total_usage"))
        remaining_usd = bal - tu
        total_usage_val = tu

    # 24h spend: difference between latest two history records
    if len(history) >= 2:
        spend_24h_val = max(
            0.0,
            to_float(history[-1].get("total_usage"))
            - to_float(history[-2].get("total_usage")),
        )
    elif history:
        spend_24h_val = to_float(history[-1].get("usage_daily_computed"))

    if is_ru:
        lines.append("💳 Финансы")
        lines.append("-" * 40)
    else:
        lines.append("Financial Summary")
        lines.append("-" * 40)

    if remaining_usd is not None:
        rub_part = ""
        if usd_rub:
            rub_part = f" (~{remaining_usd * usd_rub:.2f} {_currency_symbol(is_ru, rub=True)})"
        label = "Остаток сейчас" if is_ru else "Remaining balance"
        lines.append(f"  {label}: {fmt_usd(remaining_usd)}{rub_part}")

    rub_part = ""
    if usd_rub:
        rub_part = f" (~{spend_24h_val * usd_rub:.2f} {_currency_symbol(is_ru, rub=True)})"
    label = "Потрачено за 24ч" if is_ru else "24h spend"
    lines.append(f"  {label}: {fmt_usd(spend_24h_val)}{rub_part}")

    if total_usage_val is not None:
        rub_part = ""
        if usd_rub:
            rub_part = f" (~{total_usage_val * usd_rub:.2f} {_currency_symbol(is_ru, rub=True)})"
        label = "Общий расход" if is_ru else "Total usage"
        lines.append(f"  {label}: {fmt_usd(total_usage_val)}{rub_part}")

    if usd_rub:
        label = "Курс" if is_ru else "Rate"
        lines.append(f"  {label} USD/RUB: {usd_rub:.2f}")
    lines.append("")

    # ── 1. What is anomalous ─────────────────────────────────────
    if is_ru:
        lines.append("1. Что именно аномально")
        lines.append("-" * 40)
    else:
        lines.append("1. What is anomalous")
        lines.append("-" * 40)

    if not anomalies:
        msg = "  anomaly.json exists but contains no anomaly entries (stale)."
        if is_ru:
            msg = "  anomaly.json существует, но не содержит записей об аномалиях (устарел)."
        lines.append(msg)
    for a in anomalies:
        severity = a.get("severity", "unknown")
        anom_type = a.get("type", "unknown")
        message = a.get("message", "(no message)")
        value = a.get("value", "N/A")
        threshold = a.get("threshold", "N/A")

        if is_ru:
            sev_icon = "🔴" if severity == "critical" else "⚠️" if severity == "warning" else "ℹ️"
            lines.append(f"  {sev_icon} [{severity.upper()}] {anom_type}")
            lines.append(f"     {message}")
            lines.append(f"     Значение: {value}, Порог: {threshold}")
        else:
            icon = "[!]" if severity in ("critical", "warning") else "[i]"
            lines.append(f"  {icon} [{severity.upper()}] {anom_type}")
            lines.append(f"     {message}")
            lines.append(f"     Value: {value}, Threshold: {threshold}")

        if "growth_pct" in a:
            gval = a["growth_pct"]
            gavg = fmt_usd(a.get("avg_prev", 0))
            if is_ru:
                lines.append(f"     Рост: {gval}% (среднее ранее: {gavg})")
            else:
                lines.append(f"     Growth: {gval}% (avg prev: {gavg})")
    lines.append("")

    # ── 2. How much has spend grown ──────────────────────────────
    if is_ru:
        lines.append("2. Насколько вырос расход")
        lines.append("-" * 40)
    else:
        lines.append("2. Spend growth over time")
        lines.append("-" * 40)

    if len(history) >= 2:
        earliest = to_float(history[0].get("total_usage"))
        latest = to_float(history[-1].get("total_usage"))
        diff = latest - earliest
        pct = ((latest / earliest) - 1) * 100 if earliest > 0 else 0
        span = len(history)
        if is_ru:
            lines.append(f"  За {span} снимков: с {fmt_usd(earliest)} до {fmt_usd(latest)}")
            lines.append(f"  Прирост: {fmt_usd(diff)} ({pct:+.1f}%)")
        else:
            lines.append(f"  Over {span} snapshots: {fmt_usd(earliest)} → {fmt_usd(latest)}")
            lines.append(f"  Growth: {fmt_usd(diff)} ({pct:+.1f}%)")
    else:
        if is_ru:
            lines.append("  Недостаточно данных для оценки динамики.")
        else:
            lines.append("  Not enough data to estimate growth trend.")
    lines.append("")

    # ── 3. Possible causes ───────────────────────────────────────
    if is_ru:
        lines.append("3. Возможные причины")
        lines.append("-" * 40)
        lines.append("  - 🔄 Сбойный цикл (retry loop): многократные запросы к одной модели")
        lines.append("  - 💰 Переход на дорогую модель: смена модели или провайдера")
        lines.append("  - 📦 Неожиданные задания: cron/fork вне расписания")
        lines.append("  - 🔁 Повторные запросы: ошибки rate-limit или таймауты")
        lines.append("  - ⚙️ Проблемы конфигурации: смена model.default, увеличение max_tokens")
    else:
        lines.append("3. Possible causes")
        lines.append("-" * 40)
        lines.append("  - Retry loop: repeated requests to the same model")
        lines.append("  - Model/provider switch: changed to a more expensive model")
        lines.append("  - Unexpected tasks: cron jobs or forks outside schedule")
        lines.append("  - Repeated requests: rate-limit errors or timeouts causing retries")
        lines.append("  - Configuration issues: changed model.default, increased max_tokens")
    lines.append("")

    # ── 4. Manual checks ─────────────────────────────────────────
    if is_ru:
        lines.append("4. Что проверить вручную в OpenRouter")
        lines.append("-" * 40)
        lines.append("  - https://openrouter.ai/activity — почасовая активность")
        lines.append("  - https://openrouter.ai/keys — активные ключи и лимиты")
        lines.append("  - https://openrouter.ai/limits — rate limits и квоты")
        lines.append("  - https://openrouter.ai/credits — баланс и история списаний")
        lines.append("  - Проверить model и max_tokens в ~/.hermes/config.yaml")
        lines.append("  - Проверить cron-задачи: hermes cron list")
    else:
        lines.append("4. Manual checks in OpenRouter")
        lines.append("-" * 40)
        lines.append("  - https://openrouter.ai/activity — hourly activity")
        lines.append("  - https://openrouter.ai/keys — active keys and limits")
        lines.append("  - https://openrouter.ai/limits — rate limits and quotas")
        lines.append("  - https://openrouter.ai/credits — balance and spend history")
        lines.append("  - Check model and max_tokens in Hermes config")
        lines.append("  - Check cron jobs: hermes cron list")
    lines.append("")

    # ── 5. What to adjust ────────────────────────────────────────
    if is_ru:
        lines.append("5. Что изменить в watchdog порогах или расписании")
        lines.append("-" * 40)
        lines.append("  - Пороги в openrouter_watchdog.py (через переменные окружения):")
    else:
        lines.append("5. Watchdog thresholds or schedule adjustments")
        lines.append("-" * 40)
        lines.append("  - Thresholds in openrouter_watchdog.py (via environment variables):")

    if is_ru:
        lines.append("    • OPENROUTER_DAILY_THRESHOLD_USD — порог дневного расхода")
        lines.append("    • OPENROUTER_BALANCE_THRESHOLD_USD — порог остатка")
        lines.append("    • OPENROUTER_TOTAL_USAGE_THRESHOLD_USD — порог общего расхода")
        lines.append("    • OPENROUTER_DAILY_SPIKE_PCT — порог роста в %")
    else:
        lines.append("    • OPENROUTER_DAILY_THRESHOLD_USD — daily spend threshold")
        lines.append("    • OPENROUTER_BALANCE_THRESHOLD_USD — balance threshold")
        lines.append("    • OPENROUTER_TOTAL_USAGE_THRESHOLD_USD — total usage threshold")
        lines.append("    • OPENROUTER_DAILY_SPIKE_PCT — daily spike threshold (%)")
    lines.append("  - Adjust cron interval.")
    lines.append("  - Lower DAILY_SPIKE_PCT for more sensitive spike detection.")
    lines.append("")

    # ── Footer ───────────────────────────────────────────────────
    lines.append("=" * 55)
    lines.append(f"  {'End of report' if not is_ru else 'Конец отчёта'}")
    lines.append("=" * 55)

    return "\n".join(lines)


def _currency_symbol(is_ru: bool, rub: bool = False) -> str:
    """Return currency symbol based on language context."""
    if rub:
        return "₽" if is_ru else "RUB"
    return "$"


# ── CLI entry point ────────────────────────────────────────────────
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenRouter Anomaly Analyzer — alert-only by default.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print status even when no anomaly (for local CLI use).",
    )
    parser.add_argument(
        "--show-rub",
        action="store_true",
        help="Include USD/RUB conversion in financial summary.",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ru"],
        default="en",
        help="Output language (default: en). 'ru' enables Russian text and emoji.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    anomaly = read_json("anomaly.json")

    if anomaly is None:
        if args.verbose:
            if args.lang == "ru":
                print("Новых аномалий по OpenRouter не обнаружено.")
            else:
                print("No OpenRouter anomalies detected.")
        else:
            # [SILENT] suppresses cron delivery — nothing reaches the user
            print("[SILENT]")
        return 0

    status = read_json("status.json")
    history = read_jsonl_tail("usage_history.jsonl", n=50)

    usd_rub = get_usd_rub() if args.show_rub else None

    if args.lang == "ru":
        report = build_report_ru(status or {}, history, anomaly, usd_rub)
    else:
        report = build_report_en(status or {}, history, anomaly, usd_rub)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

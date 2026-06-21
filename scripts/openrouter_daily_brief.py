#!/usr/bin/env python3
"""OpenRouter Daily Brief — periodic summary of balance and usage.

Fetches credits from OpenRouter API, computes remaining balance and 24h
spend, and prints a formatted report. Designed for no_agent=True cron
delivery (the output is delivered directly to the user).

Usage:
  python3 scripts/openrouter_daily_brief.py              # English, USD only
  python3 scripts/openrouter_daily_brief.py --show-rub    # Include RUB conversion
  python3 scripts/openrouter_daily_brief.py --lang ru     # Russian output

Requires: OPENROUTER_API_KEY environment variable.
Uses only stdlib (urllib).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


# ── Paths ───────────────────────────────────────────────────────────
BASE_DIR = os.environ.get(
    "OPENROUTER_WATCHDOG_BASE_DIR",
    "/opt/data/openrouter-watchdog",
)
STATE_DIR = os.environ.get(
    "OPENROUTER_WATCHDOG_STATE_DIR",
    os.path.join(BASE_DIR, "state"),
)

# ── API ─────────────────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
ER_API_URL = "https://open.er-api.com/v6/latest/USD"
HTTP_TIMEOUT = 20


def _or_api_get(path: str) -> dict | None:
    """GET an OpenRouter API endpoint; return parsed JSON or None."""
    if not OPENROUTER_API_KEY:
        return None
    url = f"{OPENROUTER_API_BASE}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
        print(f"[brief] API GET {path} failed: {exc}", file=sys.stderr)
        return None


# ── Exchange rate ───────────────────────────────────────────────────
ER_API_TIMEOUT = 15


def get_usd_rub() -> float | None:
    """Fetch USD/RUB rate from open.er-api.com."""
    try:
        with urllib.request.urlopen(ER_API_URL, timeout=ER_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            rate = data.get("rates", {}).get("RUB")
            if rate:
                return float(rate)
    except Exception:
        pass
    return None


# ── History helpers ────────────────────────────────────────────────
def read_history() -> list[dict]:
    """Read usage_history.jsonl from state directory."""
    path = os.path.join(STATE_DIR, "usage_history.jsonl")
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
    return records


def compute_spend_24h_from_history(
    history: list[dict],
    now_epoch: float | None = None,
) -> float:
    """Compute usage over the last 24h using a time-based window.

    Uses epoch timestamps to find the snapshot closest to (now - 24h),
    then returns the delta from that snapshot to the latest record.
    This is more accurate than assuming a fixed number of records = 24h.
    """
    if not history:
        return 0.0

    if now_epoch is None:
        now_epoch = time.time()

    target = now_epoch - 24 * 3600

    before = None
    after = None
    for rec in history:
        try:
            e = float(rec.get("epoch", 0))
            tu = float(rec.get("total_usage", 0))
        except (TypeError, ValueError):
            continue

        if e <= target:
            if before is None or e > before.get("epoch", 0):
                before = {"epoch": e, "total": tu}
        if e >= target:
            if after is None or e < after.get("epoch", 0):
                after = {"epoch": e, "total": tu}

    if before:
        prev_total = before["total"]
    elif after:
        prev_total = after["total"]
    else:
        return 0.0

    latest_total = float(history[-1].get("total_usage", 0) or 0.0)
    return max(0.0, latest_total - prev_total)


# ── Report formatter ───────────────────────────────────────────────
def fmt_usd(v: float) -> str:
    return f"${v:.2f}"


def fmt_rub(v: float) -> str:
    return f"{v:.2f} RUB"


def build_report_en(
    remaining_balance: float,
    total_usage: float,
    spend_24h: float,
    spend_24h_history: float,
    usd_rub: float | None,
    now_date: str,
) -> str:
    """Build morning report in English (default)."""
    lines: list[str] = []
    lines.append("=" * 50)
    lines.append(f"  OpenRouter Daily Brief — {now_date}")
    lines.append("=" * 50)
    lines.append(f"  Remaining balance:  {fmt_usd(remaining_balance)}")
    lines.append(f"  Total usage:        {fmt_usd(total_usage)}")

    if usd_rub:
        lines.append(f"  Remaining (RUB):    {fmt_rub(remaining_balance * usd_rub)}")
        lines.append(f"  Total usage (RUB):  {fmt_rub(total_usage * usd_rub)}")

    lines.append(f"  24h spend:          {fmt_usd(spend_24h)}")
    if usd_rub:
        lines.append(f"  24h spend (RUB):    {fmt_rub(spend_24h * usd_rub)}")
        lines.append(f"  USD/RUB rate:       {usd_rub:.2f}")

    if spend_24h_history > 0 and abs(spend_24h_history - spend_24h) > 0.001:
        lines.append(f"  24h spend (history window): {fmt_usd(spend_24h_history)}")

    lines.append("=" * 50)
    return "\n".join(lines)


def build_report_ru(
    remaining_balance: float,
    total_usage: float,
    spend_24h: float,
    spend_24h_history: float,
    usd_rub: float | None,
    now_date: str,
) -> str:
    """Build morning report in Russian with emoji."""
    lines: list[str] = []
    lines.append("━" * 45)
    lines.append(f"  💳 OpenRouter — утренний отчёт {now_date}")
    lines.append("━" * 45)
    lines.append(f"  Остаток сейчас:  {fmt_usd(remaining_balance)}")
    lines.append(f"  Общий расход:    {fmt_usd(total_usage)}")

    if usd_rub:
        lines.append(f"  Остаток (~):     {fmt_rub(remaining_balance * usd_rub)}")
        lines.append(f"  Общий расход (~): {fmt_rub(total_usage * usd_rub)}")

    lines.append(f"  Потрачено за 24ч: {fmt_usd(spend_24h)}")
    if usd_rub:
        lines.append(f"  За 24ч (~):      {fmt_rub(spend_24h * usd_rub)}")
        lines.append(f"  Курс USD/RUB:    {usd_rub:.2f}")

    if spend_24h_history > 0 and abs(spend_24h_history - spend_24h) > 0.001:
        lines.append(f"  24ч (history window): {fmt_usd(spend_24h_history)}")

    lines.append("━" * 45)
    return "\n".join(lines)


# ── CLI entry point ────────────────────────────────────────────────
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenRouter Daily Brief — periodic summary of balance and usage.",
    )
    parser.add_argument(
        "--show-rub",
        action="store_true",
        help="Include USD/RUB conversion in the report.",
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

    # 1. Get OpenRouter credits
    raw_credits = _or_api_get("/credits")
    if not raw_credits or not isinstance(raw_credits, dict):
        print("[brief] Failed to fetch credits — aborting", file=sys.stderr)
        return 1

    if "data" in raw_credits:
        credits_data = raw_credits["data"]
    else:
        credits_data = raw_credits
    total_credits = float(credits_data.get("total_credits", 0) or 0.0)
    total_usage = float(credits_data.get("total_usage", 0) or 0.0)
    remaining_balance = total_credits - total_usage

    # 2. Get usage_daily from /auth/key (optional enrichment)
    raw_key = _or_api_get("/auth/key")
    if raw_key and isinstance(raw_key, dict) and "data" in raw_key:
        key_data = raw_key["data"]
    else:
        key_data = raw_key or {}
    usage_daily = float(key_data.get("usage_daily", 0.0) or 0.0)

    # 3. Compute 24h spend from usage_history (time-based window)
    history = read_history()
    spend_24h_history = compute_spend_24h_from_history(history) if history else 0.0

    # Use usage_daily as the primary 24h metric (provider's own calculation)
    spend_24h = usage_daily

    # 4. Optional: USD/RUB exchange rate
    usd_rub = get_usd_rub() if args.show_rub else None

    # 5. Format and print report
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.lang == "ru":
        report = build_report_ru(
            remaining_balance, total_usage, spend_24h,
            spend_24h_history, usd_rub, now_date,
        )
    else:
        report = build_report_en(
            remaining_balance, total_usage, spend_24h,
            spend_24h_history, usd_rub, now_date,
        )

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

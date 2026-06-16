#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_jsonl_tail(path: Path, limit: int = 24) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    result: List[Dict[str, Any]] = []
    for line in lines:
        try:
            payload = json.loads(line)
            if isinstance(payload, dict):
                result.append(payload)
        except Exception:
            continue
    return result


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def fmt_money(value: float) -> str:
    return f"${value:.2f}"


def main() -> int:
    base_dir = Path(os.getenv("OPENROUTER_WATCHDOG_BASE_DIR", "/opt/data/openrouter-watchdog"))
    state_dir = Path(os.getenv("OPENROUTER_WATCHDOG_STATE_DIR", str(base_dir / "state")))

    status = read_json(state_dir / "status.json", {})
    history = read_jsonl_tail(state_dir / "usage_history.jsonl", limit=24)

    current_balance = to_float(status.get("balance"))
    current_daily = to_float(status.get("usage_daily_computed"))
    current_total = to_float(status.get("total_usage"))

    max_daily = current_daily
    min_balance = current_balance

    for item in history:
        max_daily = max(max_daily, to_float(item.get("usage_daily_computed")))
        min_balance = min(min_balance, to_float(item.get("balance"), current_balance))

    brief = {
        "headline": "OpenRouter daily brief",
        "timestamp": status.get("timestamp"),
        "summary": {
            "current_balance": fmt_money(current_balance),
            "current_daily_spend": fmt_money(current_daily),
            "current_total_usage": fmt_money(current_total),
            "max_observed_daily_spend": fmt_money(max_daily),
            "min_observed_balance": fmt_money(min_balance),
        },
        "notes": [
            "This report is optional and intended for periodic owner-facing summaries.",
            "Local currency conversion should only be enabled if explicitly requested by the owner.",
        ],
    }

    sys.stdout.write(json.dumps(brief, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
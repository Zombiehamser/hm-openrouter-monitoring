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


def format_money(value: Any) -> str:
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "n/a"


def build_summary(status: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
    daily = status.get("usage_daily_computed")
    balance = status.get("balance")

    headline = "OpenRouter anomaly detected"
    if not anomalies:
        headline = "No OpenRouter anomaly detected"

    items = []
    for item in anomalies:
        items.append(
            {
                "type": item.get("type"),
                "severity": item.get("severity"),
                "message": item.get("message"),
                "value": item.get("value"),
                "threshold": item.get("threshold"),
            }
        )

    return {
        "headline": headline,
        "current_status": {
            "balance": format_money(balance),
            "daily_spend": format_money(daily),
            "key_label": status.get("key_label", "default"),
            "timestamp": status.get("timestamp"),
        },
        "anomalies": items,
        "operator_summary": build_operator_summary(status, anomalies),
    }


def build_operator_summary(status: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> str:
    if not anomalies:
        return "No anomaly is currently present. No operator action is required."

    parts = []
    daily = status.get("usage_daily_computed")
    balance = status.get("balance")

    if daily is not None:
        parts.append(f"Current computed daily spend is {format_money(daily)}.")
    if balance is not None:
        parts.append(f"Current balance is {format_money(balance)}.")

    for item in anomalies:
        message = item.get("message")
        if message:
            parts.append(str(message) + "." if not str(message).endswith(".") else str(message))

    parts.append("Check recent model usage, automation bursts, and whether thresholds should be adjusted.")
    return " ".join(parts)


def main() -> int:
    base_dir = Path(os.getenv("OPENROUTER_WATCHDOG_BASE_DIR", "/opt/data/openrouter-watchdog"))
    state_dir = Path(os.getenv("OPENROUTER_WATCHDOG_STATE_DIR", str(base_dir / "state")))

    status = read_json(state_dir / "status.json", {})
    anomaly_payload = read_json(state_dir / "anomaly.json", {})

    anomalies = anomaly_payload.get("anomalies", [])
    if not isinstance(anomalies, list):
        anomalies = []

    summary = build_summary(status, anomalies)
    sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
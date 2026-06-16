#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests


OPENROUTER_CREDITS_URL = "https://openrouter.ai/api/v1/credits"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


@dataclass
class Config:
    api_key: str
    base_dir: Path
    state_dir: Path
    state_file: Path
    status_file: Path
    anomaly_file: Path
    history_file: Path
    heartbeat_file: Path
    daily_threshold_usd: float
    balance_threshold_usd: float
    timeout_seconds: int
    key_label: str


def load_config() -> Config:
    base_dir = Path(os.getenv("OPENROUTER_WATCHDOG_BASE_DIR", "/opt/data/openrouter-watchdog"))
    state_dir = Path(os.getenv("OPENROUTER_WATCHDOG_STATE_DIR", str(base_dir / "state")))
    state_file = Path(os.getenv("OPENROUTER_WATCHDOG_STATE_FILE", str(state_dir / "daily_state.json")))

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required")

    return Config(
        api_key=api_key,
        base_dir=base_dir,
        state_dir=state_dir,
        state_file=state_file,
        status_file=state_dir / "status.json",
        anomaly_file=state_dir / "anomaly.json",
        history_file=state_dir / "usage_history.jsonl",
        heartbeat_file=state_dir / "heartbeat.epoch",
        daily_threshold_usd=float(os.getenv("OPENROUTER_DAILY_THRESHOLD_USD", "5.0")),
        balance_threshold_usd=float(os.getenv("OPENROUTER_BALANCE_THRESHOLD_USD", "3.0")),
        timeout_seconds=int(os.getenv("OPENROUTER_HTTP_TIMEOUT_SECONDS", "20")),
        key_label=os.getenv("OPENROUTER_KEY_LABEL", "default"),
    )


def fetch_credits(cfg: Config) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Accept": "application/json",
    }
    response = requests.get(OPENROUTER_CREDITS_URL, headers=headers, timeout=cfg.timeout_seconds)
    response.raise_for_status()
    payload = response.json()

    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected OpenRouter response format")

    return data


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_status(cfg: Config, credits: Dict[str, Any], previous_state: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = utc_now_iso()
    now_epoch = time.time()

    total_usage = to_float(credits.get("total_usage"))
    balance = to_float(credits.get("total_credits")) - total_usage
    usage_daily_api = to_float(credits.get("usage_daily"))

    last_total_usage = to_float(previous_state.get("last_total_usage"), total_usage)
    usage_daily_computed = max(0.0, total_usage - last_total_usage)

    return {
        "timestamp": now_iso,
        "epoch": now_epoch,
        "balance": round(balance, 6),
        "total_usage": round(total_usage, 6),
        "usage_daily": round(usage_daily_computed, 6),
        "usage_daily_computed": round(usage_daily_computed, 6),
        "usage_daily_api": round(usage_daily_api, 6),
        "key_label": cfg.key_label,
    }


def detect_anomalies(cfg: Config, status: Dict[str, Any]) -> List[Dict[str, Any]]:
    anomalies: List[Dict[str, Any]] = []
    detected_at = status["timestamp"]

    usage_daily = to_float(status.get("usage_daily_computed"))
    balance = to_float(status.get("balance"))

    if usage_daily >= cfg.daily_threshold_usd:
        anomalies.append(
            {
                "type": "daily_usage_high",
                "severity": "warning",
                "value": round(usage_daily, 6),
                "threshold": round(cfg.daily_threshold_usd, 6),
                "message": f"Daily spend ${usage_daily:.2f} >= ${cfg.daily_threshold_usd:.2f}",
                "detected_at": detected_at,
            }
        )

    if balance <= cfg.balance_threshold_usd:
        anomalies.append(
            {
                "type": "balance_low",
                "severity": "critical",
                "value": round(balance, 6),
                "threshold": round(cfg.balance_threshold_usd, 6),
                "message": f"Balance ${balance:.2f} <= ${cfg.balance_threshold_usd:.2f}",
                "detected_at": detected_at,
            }
        )

    return anomalies


def build_state(status: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "last_run": status["timestamp"],
        "last_total_usage": status["total_usage"],
        "last_balance": status["balance"],
    }


def main() -> int:
    try:
        cfg = load_config()
        cfg.state_dir.mkdir(parents=True, exist_ok=True)

        previous_state = read_json(cfg.state_file, {})
        credits = fetch_credits(cfg)
        status = build_status(cfg, credits, previous_state)
        anomalies = detect_anomalies(cfg, status)
        state = build_state(status)

        write_json(cfg.status_file, status)
        write_json(cfg.state_file, state)
        append_jsonl(cfg.history_file, status)
        cfg.heartbeat_file.write_text(f"{int(status['epoch'])}\n", encoding="utf-8")

        if anomalies:
            anomaly_payload = {
                "detected_at": status["timestamp"],
                "epoch": status["epoch"],
                "anomalies": anomalies,
            }
            write_json(cfg.anomaly_file, anomaly_payload)
        elif cfg.anomaly_file.exists():
            cfg.anomaly_file.unlink()

        return 0

    except Exception as exc:
        error_payload = {
            "detected_at": utc_now_iso(),
            "epoch": time.time(),
            "anomalies": [
                {
                    "type": "watchdog_error",
                    "severity": "critical",
                    "value": 0,
                    "threshold": 0,
                    "message": str(exc),
                    "detected_at": utc_now_iso(),
                }
            ],
        }
        try:
            base_dir = Path(os.getenv("OPENROUTER_WATCHDOG_BASE_DIR", "/opt/data/openrouter-watchdog"))
            state_dir = Path(os.getenv("OPENROUTER_WATCHDOG_STATE_DIR", str(base_dir / "state")))
            write_json(state_dir / "anomaly.json", error_payload)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
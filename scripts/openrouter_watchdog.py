#!/usr/bin/env python3
"""
OpenRouter Watchdog — collects balance and usage metrics from OpenRouter API.

Designed for no_agent=True Hermes cron jobs. Uses only stdlib (zero external deps).

Architecture (daily spend):
  Primary:    computed delta of total_usage between runs (deterministic, field: usage_daily_computed)
  Fallback:   usage_daily from /auth/key (provider's own 24h window, field: usage_daily_api)
  Enrichment: key_label from /auth/key for multi-key identification
  Raw dumps:  disabled by default; set OPENROUTER_SAVE_RAW_RESPONSES=true to enable
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ── Constants ─────────────────────────────────────────────────────
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
CREDITS_PATH = "/credits"
AUTH_KEY_PATH = "/auth/key"


# ── Defaults via env vars ─────────────────────────────────────────
def env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


def env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR = env_str("OPENROUTER_WATCHDOG_BASE_DIR", "/opt/data/openrouter-watchdog")
STATE_DIR = env_str("OPENROUTER_WATCHDOG_STATE_DIR", os.path.join(BASE_DIR, "state"))

# ── API ───────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
HTTP_TIMEOUT = env_float("OPENROUTER_HTTP_TIMEOUT_SECONDS", 20.0)

# ── Thresholds ────────────────────────────────────────────────────
DAILY_THRESHOLD = env_float("OPENROUTER_DAILY_THRESHOLD_USD", 5.0)
BALANCE_THRESHOLD = env_float("OPENROUTER_BALANCE_THRESHOLD_USD", 3.0)
TOTAL_USAGE_THRESHOLD = env_float("OPENROUTER_TOTAL_USAGE_THRESHOLD_USD", 50.0)
DAILY_SPIKE_PCT = env_float("OPENROUTER_DAILY_SPIKE_PCT", 300.0)

# ── Debug —────────────────────────────────────────────────────────
SAVE_RAW_RESPONSES = env_bool("OPENROUTER_SAVE_RAW_RESPONSES", False)


# ── Helpers ───────────────────────────────────────────────────────
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _epoch() -> float:
    return time.time()


def _api_get(path: str) -> dict | None:
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
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"[watchdog] API GET {path} failed: {exc}", file=sys.stderr)
        return None


def _ensure_state_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


def _write_json(filename: str, data: Any) -> None:
    path = os.path.join(STATE_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"[watchdog] wrote {path}")


def _append_jsonl(filename: str, record: dict) -> None:
    path = os.path.join(STATE_DIR, filename)
    with open(path, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _read_json(filename: str) -> dict | list | None:
    path = os.path.join(STATE_DIR, filename)
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _read_jsonl(filename: str) -> list[dict]:
    path = os.path.join(STATE_DIR, filename)
    if not os.path.isfile(path):
        return []
    records: list[dict] = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        pass
    return records


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ── Collectors ────────────────────────────────────────────────────
def get_credits() -> dict | None:
    """GET /credits — returns {total_credits, total_usage} or None."""
    raw = _api_get(CREDITS_PATH)
    if raw and isinstance(raw, dict) and "data" in raw:
        return raw["data"]
    return raw


def get_key_info() -> dict | None:
    """GET /auth/key — returns key metadata (usage_daily, label) or None.

    This endpoint may not be available for all API keys (permissions).
    Returns None gracefully when unavailable.
    """
    raw = _api_get(AUTH_KEY_PATH)
    if raw and isinstance(raw, dict) and "data" in raw:
        return raw["data"]
    return raw


# ── Anomaly Detection ─────────────────────────────────────────────
def check_anomalies(
    credits: dict | None,
    key_info: dict | None,
    usage_history: list[dict],
) -> list[dict]:
    """Return list of anomaly dicts — empty list = all clear.

    Anomaly types detected:
      - total_usage_high:  total usage >= TOTAL_USAGE_THRESHOLD
      - daily_usage_high:  computed daily spend >= DAILY_THRESHOLD
      - balance_low:       remaining balance <= BALANCE_THRESHOLD
      - daily_usage_spike: daily spend >= DAILY_SPIKE_PCT of 7-day avg
    """
    anomalies: list[dict] = []
    now = _utc_now_iso()

    # ── from /credits ──
    if credits:
        total_credits = _to_float(credits.get("total_credits"))
        total_usage_val = _to_float(credits.get("total_usage"))
        balance = total_credits - total_usage_val

        if total_usage_val >= TOTAL_USAGE_THRESHOLD:
            anomalies.append({
                "type": "total_usage_high",
                "severity": "warning",
                "value": round(total_usage_val, 6),
                "threshold": round(TOTAL_USAGE_THRESHOLD, 6),
                "message": f"Total usage ${total_usage_val:.2f} >= ${TOTAL_USAGE_THRESHOLD:.2f}",
                "detected_at": now,
            })

        if balance <= BALANCE_THRESHOLD:
            anomalies.append({
                "type": "balance_low",
                "severity": "critical",
                "value": round(balance, 6),
                "threshold": round(BALANCE_THRESHOLD, 6),
                "message": f"Balance ${balance:.2f} <= ${BALANCE_THRESHOLD:.2f}",
                "detected_at": now,
            })

    # ── from usage_history (daily absolute threshold and growth spike) ──
    recent = [r for r in usage_history if "usage_daily_computed" in r]

    # Absolute daily threshold: check against the most recent record
    if recent:
        today = recent[-1]
        daily_today = _to_float(today.get("usage_daily_computed"))

        if daily_today >= DAILY_THRESHOLD:
            anomalies.append({
                "type": "daily_usage_high",
                "severity": "warning",
                "value": round(daily_today, 6),
                "threshold": round(DAILY_THRESHOLD, 6),
                "message": f"Daily spend ${daily_today:.2f} >= ${DAILY_THRESHOLD:.2f}",
                "detected_at": now,
            })

    # Growth spike: needs at least 2 records for a meaningful average
    if len(recent) >= 2:
        today = recent[-1]
        prev = recent[:-1]
        daily_today = _to_float(today.get("usage_daily_computed"))
        daily_avg = sum(_to_float(r.get("usage_daily_computed")) for r in prev) / len(prev)

        if daily_avg > 0 and (daily_today / daily_avg * 100) >= DAILY_SPIKE_PCT:
            anomalies.append({
                "type": "daily_usage_spike",
                "severity": "warning",
                "value": round(daily_today, 6),
                "avg_prev": round(daily_avg, 6),
                "growth_pct": round(daily_today / daily_avg * 100, 1),
                "threshold_pct": round(DAILY_SPIKE_PCT, 1),
                "message": (
                    f"Daily spend ${daily_today:.2f} is "
                    f"{daily_today / daily_avg * 100:.0f}% of avg ${daily_avg:.2f} "
                    f"(threshold {DAILY_SPIKE_PCT:.0f}%)"
                ),
                "detected_at": now,
            })

    return anomalies


# ── State builders ────────────────────────────────────────────────
def build_status(
    credits: dict | None,
    key_info: dict | None,
    usage_history: list[dict],
) -> dict:
    """Build the current status snapshot."""
    now_iso = _utc_now_iso()
    now_epoch = _epoch()

    # Primary: compute daily spend from total_usage delta
    total_usage = _to_float(credits.get("total_usage")) if credits else None
    last_record = usage_history[-1] if usage_history else {}
    last_total = _to_float(last_record.get("total_usage"), total_usage or 0.0)
    usage_daily_computed = max(0.0, (total_usage or 0.0) - last_total)

    # Fallback: usage_daily from /auth/key
    usage_daily_api = _to_float(key_info.get("usage_daily")) if key_info else None

    # Enrichment: key label
    key_label = (key_info or {}).get("label", "default") if key_info else "default"

    status: dict = {
        "timestamp": now_iso,
        "epoch": now_epoch,
        "total_usage": round(total_usage, 6) if total_usage is not None else None,
        "usage_daily_computed": round(usage_daily_computed, 6),
        "key_label": key_label,
    }

    # Balance
    if credits:
        credits_total = _to_float(credits.get("total_credits"))
        usage_val = _to_float(credits.get("total_usage"))
        balance = credits_total - usage_val
        status["balance"] = round(balance, 6)
    else:
        status["balance"] = None

    # Cross-reference with API usage_daily if available
    if usage_daily_api is not None:
        status["usage_daily_api"] = round(usage_daily_api, 6)

    # Raw responses (debug only, opt-in)
    if SAVE_RAW_RESPONSES:
        status["credits_raw"] = credits
        status["key_raw"] = key_info

    return status


def build_state(status: dict) -> dict:
    """Build persistent state snapshot for next run's delta calculation."""
    return {
        "last_run": status.get("timestamp"),
        "last_total_usage": status.get("total_usage"),
        "last_balance": status.get("balance"),
    }


# ── Main ──────────────────────────────────────────────────────────
def main() -> int:
    try:
        if not OPENROUTER_API_KEY:
            print("[watchdog] ERROR: OPENROUTER_API_KEY is not set", file=sys.stderr)
            _write_error_anomaly("OPENROUTER_API_KEY is not set")
            return 1

        _ensure_state_dir()

        # Collect
        credits = get_credits()
        key_info = get_key_info()

        if not credits:
            print("[watchdog] WARNING: /credits returned no data — partial run", file=sys.stderr)

        # Read history for delta calculation and spike detection
        usage_history = _read_jsonl("usage_history.jsonl")

        # Build status
        status = build_status(credits, key_info, usage_history)

        # Write state files
        _write_json("status.json", status)
        _write_json("daily_state.json", build_state(status))
        _append_jsonl("usage_history.jsonl", status)

        # Heartbeat
        hb_path = os.path.join(STATE_DIR, "heartbeat.epoch")
        with open(hb_path, "w") as f:
            f.write(f"{int(status.get('epoch', _epoch()))}\n")
        print(f"[watchdog] wrote {hb_path}")

        # Anomaly detection — include the just-computed status in history
        # so check_anomalies sees the latest usage_daily_computed value
        full_history = list(usage_history) + [status]
        anomalies = check_anomalies(credits, key_info, full_history)
        if anomalies:
            anomaly_payload = {
                "detected_at": status.get("timestamp"),
                "epoch": status.get("epoch"),
                "anomalies": anomalies,
            }
            _write_json("anomaly.json", anomaly_payload)
            print(f"[watchdog] ⚠ {len(anomalies)} anomaly/ies detected")
        else:
            anomaly_path = os.path.join(STATE_DIR, "anomaly.json")
            if os.path.isfile(anomaly_path):
                os.remove(anomaly_path)
                print("[watchdog] cleared stale anomaly.json")
            print("[watchdog] ✅ No anomalies detected")

        print(f"[watchdog] Done at {status.get('timestamp')}")
        return 0

    except Exception as exc:
        print(f"[watchdog] UNEXPECTED ERROR: {exc}", file=sys.stderr)
        _write_error_anomaly(str(exc))
        return 1


def _write_error_anomaly(message: str) -> None:
    """Write an error anomaly payload when the watchdog itself fails."""
    try:
        _ensure_state_dir()
        error_payload = {
            "detected_at": _utc_now_iso(),
            "epoch": _epoch(),
            "anomalies": [
                {
                    "type": "watchdog_error",
                    "severity": "critical",
                    "value": 0,
                    "threshold": 0,
                    "message": message,
                    "detected_at": _utc_now_iso(),
                }
            ],
        }
        _write_json("anomaly.json", error_payload)
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())

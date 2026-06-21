"""Tests for openrouter_watchdog.py — deterministic logic only (no network).

check_anomalies receives the full history INCLUDING the just-computed status
record (as main() does). Tests simulate this by including the expected
computed values in the last history entry.
"""

from scripts.openrouter_watchdog import build_state, build_status, check_anomalies


def test_build_state_uses_status_fields():
    """build_state extracts the right fields for next-run delta calculation."""
    status = {
        "timestamp": "2026-06-16T09:00:00+00:00",
        "total_usage": 10.23,
        "balance": 12.84,
    }

    state = build_state(status)

    assert state["last_run"] == "2026-06-16T09:00:00+00:00"
    assert state["last_total_usage"] == 10.23
    assert state["last_balance"] == 12.84


def test_build_status_daily_computed_from_history():
    """usage_daily_computed is the delta of total_usage vs last record."""
    credits = {"total_credits": 30.0, "total_usage": 15.50}
    key_info = None
    usage_history = [
        {"timestamp": "...", "total_usage": 10.0, "usage_daily_computed": 5.0},
    ]

    status = build_status(credits, key_info, usage_history)

    assert status["total_usage"] == 15.50
    assert status["usage_daily_computed"] == 5.50  # 15.50 - 10.0
    assert status["balance"] == 14.50  # 30.0 - 15.50
    assert status["key_label"] == "default"


def test_build_status_no_history():
    """Without history, usage_daily_computed defaults to 0 (no delta)."""
    credits = {"total_credits": 30.0, "total_usage": 15.50}
    key_info = None

    status = build_status(credits, key_info, [])

    assert status["usage_daily_computed"] == 0.0
    assert status["balance"] == 14.50


def test_build_status_no_credits():
    """Without credits data, balance and total_usage are None."""
    status = build_status(None, None, [])

    assert status["total_usage"] is None
    assert status["balance"] is None
    assert status["usage_daily_computed"] == 0.0


def test_build_status_with_key_info():
    """key_info enriches status with key_label and usage_daily_api."""
    credits = {"total_credits": 30.0, "total_usage": 5.0}
    key_info = {"usage_daily": 2.50, "label": "my-key"}
    usage_history = [{"timestamp": "...", "total_usage": 3.0, "usage_daily_computed": 1.0}]

    status = build_status(credits, key_info, usage_history)

    assert status["key_label"] == "my-key"
    assert status["usage_daily_api"] == 2.50
    assert status["usage_daily_computed"] == 2.0  # 5.0 - 3.0


def test_check_anomalies_daily_usage_high():
    """Anomaly when daily computed spend >= threshold (default $5).

    Simulates what main() passes: full_history includes the just-computed status,
    so the last record has the actual usage_daily_computed = 6.45.
    """
    credits = {"total_credits": 30.0, "total_usage": 6.45}
    key_info = None
    full_history = [
        {"timestamp": "2026-06-15T09:00:00", "total_usage": 0.0, "usage_daily_computed": 0.0},
        # This simulates the new status appended by main() before anomaly check
        {"timestamp": "2026-06-16T09:00:00", "total_usage": 6.45, "usage_daily_computed": 6.45},
    ]

    anomalies = check_anomalies(credits, key_info, full_history)

    types = {a["type"] for a in anomalies}
    assert "daily_usage_high" in types


def test_check_anomalies_balance_low():
    """Anomaly when balance <= threshold (default $3)."""
    credits = {"total_credits": 5.0, "total_usage": 3.10}
    key_info = None
    full_history = [
        {"timestamp": "2026-06-16T09:00:00", "total_usage": 3.10, "usage_daily_computed": 1.0},
    ]

    anomalies = check_anomalies(credits, key_info, full_history)

    # balance = 5.0 - 3.10 = 1.90 <= 3.0 threshold
    types = {a["type"] for a in anomalies}
    assert "balance_low" in types


def test_check_anomalies_both():
    """When both daily_usage_high and balance_low are present."""
    credits = {"total_credits": 5.0, "total_usage": 15.50}
    key_info = None
    full_history = [
        {"timestamp": "2026-06-15T09:00:00", "total_usage": 0.0, "usage_daily_computed": 0.0},
        {"timestamp": "2026-06-16T09:00:00", "total_usage": 15.50, "usage_daily_computed": 15.50},
    ]

    anomalies = check_anomalies(credits, key_info, full_history)

    types = {a["type"] for a in anomalies}
    assert "daily_usage_high" in types    # 15.50 >= 5.0
    assert "balance_low" in types          # 5.0 - 15.50 <= 3.0


def test_check_anomalies_total_usage_high():
    """Anomaly when total usage >= threshold (default $50)."""
    credits = {"total_credits": 100.0, "total_usage": 50.50}
    key_info = None
    full_history = [
        {"timestamp": "2026-06-16T09:00:00", "total_usage": 50.50, "usage_daily_computed": 10.0},
    ]

    anomalies = check_anomalies(credits, key_info, full_history)

    types = {a["type"] for a in anomalies}
    assert "total_usage_high" in types


def test_check_anomalies_no_anomaly():
    """No anomalies when all values are well below thresholds."""
    credits = {"total_credits": 100.0, "total_usage": 10.0}
    key_info = None
    full_history = [
        {"timestamp": "2026-06-14T09:00:00", "total_usage": 8.0, "usage_daily_computed": 1.0},
        {"timestamp": "2026-06-15T09:00:00", "total_usage": 9.0, "usage_daily_computed": 1.0},
        {"timestamp": "2026-06-16T09:00:00", "total_usage": 10.0, "usage_daily_computed": 1.0},
    ]

    anomalies = check_anomalies(credits, key_info, full_history)

    assert anomalies == []  # balance 90, daily 1.0, total 10 all under thresholds


def test_check_anomalies_daily_usage_spike():
    """Anomaly when daily spend >= 300% of 7-day average.

    Full history: 7 low records + 1 spike record (as main() would accumulate).
    """
    full_history = []
    for i in range(7):
        full_history.append({
            "timestamp": f"2026-06-{7+i:02d}T09:00:00",
            "total_usage": float(i * 0.5),
            "usage_daily_computed": 0.5,  # consistent $0.50/day
        })
    # Spike record (the computed status for current run)
    full_history.append({
        "timestamp": "2026-06-14T09:00:00",
        "total_usage": 6.0,
        "usage_daily_computed": 2.50,  # $2.50 today = 500% of $0.50 avg
    })

    credits = {"total_credits": 100.0, "total_usage": 6.0}
    key_info = None

    anomalies = check_anomalies(credits, key_info, full_history)

    types = {a["type"] for a in anomalies}
    assert "daily_usage_spike" in types  # 2.50 / 0.50 * 100 = 500% >= 300%


def test_check_anomalies_daily_usage_spike_with_daily_usage_high():
    """Both spike AND daily_usage_high when daily exceeds both thresholds."""
    full_history = []
    for i in range(7):
        full_history.append({
            "timestamp": f"2026-06-{7+i:02d}T09:00:00",
            "total_usage": float(i * 0.5),
            "usage_daily_computed": 0.5,
        })
    full_history.append({
        "timestamp": "2026-06-14T09:00:00",
        "total_usage": 15.0,
        "usage_daily_computed": 5.50,  # $5.50 >= $5.0 threshold AND 1100% of $0.50 avg
    })

    credits = {"total_credits": 100.0, "total_usage": 15.0}
    key_info = None

    anomalies = check_anomalies(credits, key_info, full_history)

    types = {a["type"] for a in anomalies}
    assert "daily_usage_spike" in types     # 5.50/0.50 = 1100% >= 300%
    assert "daily_usage_high" in types       # 5.50 >= 5.0

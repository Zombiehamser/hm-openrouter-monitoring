from scripts.openrouter_watchdog import build_state, detect_anomalies


def test_build_state_uses_status_fields():
    status = {
        "timestamp": "2026-06-16T09:00:00+00:00",
        "total_usage": 10.23,
        "balance": 12.84,
    }

    state = build_state(status)

    assert state["last_run"] == "2026-06-16T09:00:00+00:00"
    assert state["last_total_usage"] == 10.23
    assert state["last_balance"] == 12.84


class DummyConfig:
    daily_threshold_usd = 5.0
    balance_threshold_usd = 3.0


def test_detect_anomalies_daily_usage_high():
    status = {
        "timestamp": "2026-06-16T09:00:00+00:00",
        "usage_daily_computed": 6.45,
        "balance": 12.84,
    }

    anomalies = detect_anomalies(DummyConfig(), status)

    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "daily_usage_high"


def test_detect_anomalies_low_balance():
    status = {
        "timestamp": "2026-06-16T09:00:00+00:00",
        "usage_daily_computed": 1.20,
        "balance": 2.10,
    }

    anomalies = detect_anomalies(DummyConfig(), status)

    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "balance_low"


def test_detect_anomalies_both():
    status = {
        "timestamp": "2026-06-16T09:00:00+00:00",
        "usage_daily_computed": 7.10,
        "balance": 2.10,
    }

    anomalies = detect_anomalies(DummyConfig(), status)

    types = {item["type"] for item in anomalies}
    assert types == {"daily_usage_high", "balance_low"}
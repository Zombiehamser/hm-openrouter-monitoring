"""Tests for openrouter_anomaly_analyzer.py — report formatting and silent mode."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# ── We test the public report-building functions directly ──────────
from scripts.openrouter_anomaly_analyzer import (
    build_report_en,
    build_report_ru,
    fmt_usd,
)


# ── Sample data ───────────────────────────────────────────────────
SAMPLE_HISTORY = [
    {"timestamp": f"2026-06-{15 + i:02d}T10:00:00+00:00",
     "total_usage": 39.0 + i * 0.8,
     "usage_daily_computed": 0.8 + i * 0.05}
    for i in range(7)
]
SAMPLE_HISTORY.append({
    "timestamp": "2026-06-21T10:00:00+00:00",
    "total_usage": 45.50,
    "usage_daily_computed": 6.45,
})

SAMPLE_STATUS = {
    "timestamp": "2026-06-21T10:00:00+00:00",
    "epoch": 1781596800.0,
    "balance": 12.84,
    "total_usage": 45.50,
    "usage_daily_computed": 6.45,
    "key_label": "default",
}

SAMPLE_ANOMALY = {
    "detected_at": "2026-06-21T10:00:00+00:00",
    "anomalies": [
        {
            "type": "daily_usage_high",
            "severity": "warning",
            "value": 6.45,
            "threshold": 5.0,
            "message": "Daily spend $6.45 >= $5.00",
            "detected_at": "2026-06-21T10:00:00+00:00",
        },
        {
            "type": "balance_low",
            "severity": "critical",
            "value": 2.10,
            "threshold": 3.0,
            "message": "Balance $2.10 <= $3.00",
            "detected_at": "2026-06-21T10:00:00+00:00",
        },
    ],
}


# ── Tests ──────────────────────────────────────────────────────────

def test_analyzer_silent_no_anomaly():
    """main() with no anomaly.json prints [SILENT] (cron-friendly default)."""
    from scripts.openrouter_anomaly_analyzer import main

    # Create a temp state dir with no anomaly.json
    with tempfile.TemporaryDirectory() as tmpdir:
        old_state = os.environ.get("OPENROUTER_WATCHDOG_STATE_DIR")
        os.environ["OPENROUTER_WATCHDOG_STATE_DIR"] = tmpdir

        # Force re-import so STATE_DIR picks up the env var
        import importlib
        import scripts.openrouter_anomaly_analyzer as ana
        importlib.reload(ana)

        # Capture stdout
        from io import StringIO
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            exit_code = ana.main([])  # no args = default mode
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue().strip()

        # Restore env
        if old_state is not None:
            os.environ["OPENROUTER_WATCHDOG_STATE_DIR"] = old_state
        else:
            os.unsetenv("OPENROUTER_WATCHDOG_STATE_DIR")

        assert exit_code == 0
        assert output == "[SILENT]", f"Expected [SILENT], got: {output}"


def test_analyzer_silent_no_anomaly_verbose():
    """main() with --verbose prints a status message instead of [SILENT]."""
    from scripts.openrouter_anomaly_analyzer import main

    with tempfile.TemporaryDirectory() as tmpdir:
        old_state = os.environ.get("OPENROUTER_WATCHDOG_STATE_DIR")
        os.environ["OPENROUTER_WATCHDOG_STATE_DIR"] = tmpdir

        import importlib
        import scripts.openrouter_anomaly_analyzer as ana
        importlib.reload(ana)

        from io import StringIO
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            exit_code = ana.main(["--verbose"])
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue().strip()

        if old_state is not None:
            os.environ["OPENROUTER_WATCHDOG_STATE_DIR"] = old_state
        else:
            os.unsetenv("OPENROUTER_WATCHDOG_STATE_DIR")

        assert exit_code == 0
        assert output != "[SILENT]", "Verbose mode must not output [SILENT]"
        assert len(output) > 0, "Verbose mode must output something"


def test_analyzer_build_report_en_format():
    """EN report has correct structure: header, sections 1-5, no emoji."""
    report = build_report_en(SAMPLE_STATUS, SAMPLE_HISTORY, SAMPLE_ANOMALY, usd_rub=None)

    # Header
    assert "Analytical Report" in report
    assert "UTC" in report

    # All 5 sections present
    assert "1. What is anomalous" in report
    assert "2. Spend growth over time" in report
    assert "3. Possible causes" in report
    assert "4. Manual checks in OpenRouter" in report
    assert "5. Watchdog thresholds or schedule adjustments" in report

    # Anomaly types
    assert "[WARNING]" in report
    assert "[CRITICAL]" in report
    assert "daily_usage_high" in report
    assert "balance_low" in report
    assert "$6.45" in report
    assert "$2.10" in report

    # No emoji in English mode
    assert "\U0001f534" not in report  # red circle
    assert "\u26a0\ufe0f" not in report  # warning sign
    assert "\U0001f4b0" not in report  # money bag

    # No RUB
    assert "RUB" not in report
    assert "\u20bd" not in report  # ruble sign

    # Financial summary present
    assert "Financial Summary" in report
    assert "Remaining balance" in report
    assert "24h spend" in report
    assert "Total usage" in report

    # End marker
    assert "End of report" in report


def test_analyzer_build_report_ru_format():
    """RU report has Russian headers, emoji for severity, RUB conversion."""
    report_ru = build_report_ru(SAMPLE_STATUS, SAMPLE_HISTORY, SAMPLE_ANOMALY, usd_rub=85.0)

    # Russian header
    assert "\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u043e\u0442\u0447\u0451\u0442" in report_ru

    # Russian section titles
    assert "\u0427\u0442\u043e \u0438\u043c\u0435\u043d\u043d\u043e \u0430\u043d\u043e\u043c\u0430\u043b\u044c\u043d\u043e" in report_ru
    assert "\u041d\u0430\u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0432\u044b\u0440\u043e\u0441 \u0440\u0430\u0441\u0445\u043e\u0434" in report_ru
    assert "\u0412\u043e\u0437\u043c\u043e\u0436\u043d\u044b\u0435 \u043f\u0440\u0438\u0447\u0438\u043d\u044b" in report_ru
    assert "\u0427\u0442\u043e \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0432\u0440\u0443\u0447\u043d\u0443\u044e" in report_ru
    assert "\u0427\u0442\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c" in report_ru

    # Emoji for severity
    assert "\U0001f534" in report_ru  # red circle = critical
    assert "\u26a0\ufe0f" in report_ru  # warning sign = warning

    # RUB present
    assert "\u20bd" in report_ru  # ruble sign
    assert "85.00" in report_ru  # exchange rate

    # Financial section with currency
    assert "\U0001f4b3" in report_ru  # credit card emoji for "Финансы"

    # Russian end marker
    assert "\u041a\u043e\u043d\u0435\u0446 \u043e\u0442\u0447\u0451\u0442\u0430" in report_ru

    # Emoji in possible causes
    assert "\U0001f504" in report_ru  # 🔄 retry
    assert "\U0001f4b0" in report_ru  # 💰 money


def test_analyzer_fmt_usd():
    """fmt_usd formats money correctly."""
    assert fmt_usd(0.0) == "$0.0000"
    assert fmt_usd(5.0) == "$5.0000"
    assert fmt_usd(5.123456) == "$5.1235"
    assert fmt_usd(-1.50) == "$-1.5000"
    assert fmt_usd("5.0") == "$5.0000"
    assert fmt_usd(None) == "$0.0000"

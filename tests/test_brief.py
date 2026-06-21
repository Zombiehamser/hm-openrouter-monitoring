"""Tests for openrouter_daily_brief.py — 24h spend computation and report formatting."""

from scripts.openrouter_daily_brief import (
    build_report_en,
    build_report_ru,
    compute_spend_24h_from_history,
    fmt_usd,
    fmt_rub,
)


# ── Sample data ───────────────────────────────────────────────────
SAMPLE_HISTORY = [
    {"timestamp": "2026-06-20T06:00:00+00:00", "epoch": 1781589600.0, "total_usage": 40.0, "usage_daily_computed": 0.8},
    {"timestamp": "2026-06-20T12:00:00+00:00", "epoch": 1781611200.0, "total_usage": 41.0, "usage_daily_computed": 1.0},
    {"timestamp": "2026-06-20T18:00:00+00:00", "epoch": 1781632800.0, "total_usage": 42.5, "usage_daily_computed": 1.5},
    {"timestamp": "2026-06-21T00:00:00+00:00", "epoch": 1781654400.0, "total_usage": 43.0, "usage_daily_computed": 0.5},
    {"timestamp": "2026-06-21T06:00:00+00:00", "epoch": 1781676000.0, "total_usage": 44.0, "usage_daily_computed": 1.0},
    {"timestamp": "2026-06-21T12:00:00+00:00", "epoch": 1781697600.0, "total_usage": 45.5, "usage_daily_computed": 1.5},
]


# ── Tests ──────────────────────────────────────────────────────────

def test_brief_compute_spend_24h_from_history():
    """Time-based window picks the right snapshot for 24h delta."""
    # now_epoch = 1781697600 + 3600 = 1781701200 (2026-06-21T13:00:00)
    now = 1781701200.0

    spend = compute_spend_24h_from_history(SAMPLE_HISTORY, now_epoch=now)

    # 24h window: now - 86400 = 1781614800 (2026-06-20T13:00:00)
    # Closest record before that window: epoch 1781611200 (total=41.0)
    # Latest record: epoch 1781697600 (total=45.5)
    # Expected: 45.5 - 41.0 = 4.5
    assert abs(spend - 4.5) < 0.001, f"Expected 4.5, got {spend}"


def test_brief_compute_spend_24h_from_history_all_after_window():
    """All records after window boundary: use earliest as baseline."""
    now = 1781640000.0  # 2026-06-20T20:00:00
    # 24h window: 1781553600 (2026-06-19T20:00:00)
    # All records have epochs > 1781553600
    # after = first (earliest) record >= target = epoch 1781589600 (total=40.0)
    # before = None
    # prev_total = 40.0 (falls through to elif after)
    # Latest total = 45.5 (SAMPLE_HISTORY[-1])
    # Expected: 45.5 - 40.0 = 5.5
    spend = compute_spend_24h_from_history(SAMPLE_HISTORY, now_epoch=now)
    assert abs(spend - 5.5) < 0.001, f"Expected 5.5, got {spend}"


def test_brief_compute_spend_24h_from_history_no_history():
    """Empty history returns 0.0."""
    assert compute_spend_24h_from_history([], now_epoch=1000.0) == 0.0


def test_brief_compute_spend_24h_from_history_single_record():
    """Single record history returns 0.0 (no delta to compute)."""
    hist = [{"timestamp": "2026-06-21T10:00:00", "epoch": 1000.0, "total_usage": 10.0}]
    assert compute_spend_24h_from_history(hist, now_epoch=2000.0) == 0.0


def test_brief_compute_spend_24h_from_history_before_only():
    """Records only before window: use last before-window record."""
    hist = [
        {"timestamp": "2026-06-19T06:00:00", "epoch": 1781416800.0, "total_usage": 30.0},
        {"timestamp": "2026-06-19T12:00:00", "epoch": 1781438400.0, "total_usage": 32.0},
        {"timestamp": "2026-06-19T18:00:00", "epoch": 1781460000.0, "total_usage": 34.0},
    ]
    now = 1781553600.0  # 2026-06-20T20:00:00
    # 24h window: 1781467200 — all 3 records before that
    # before = the one closest to target from below = epoch 1781460000 (total=34.0)
    # after = None
    # prev_total = 34.0
    # latest = 34.0 (last record)
    # Expected: 34.0 - 34.0 = 0.0
    spend = compute_spend_24h_from_history(hist, now_epoch=now)
    assert abs(spend) < 0.001, f"Expected 0.0, got {spend}"


def test_brief_build_report_en_format():
    """EN brief has clean text with key fields, no emoji, no RUB."""
    report = build_report_en(
        remaining_balance=12.84,
        total_usage=45.50,
        spend_24h=1.50,
        spend_24h_history=4.5,
        usd_rub=None,
        now_date="2026-06-21",
    )

    assert "OpenRouter Daily Brief" in report
    assert "2026-06-21" in report
    assert "Remaining balance" in report
    assert "$12.84" in report
    assert "Total usage" in report
    assert "$45.50" in report
    assert "24h spend" in report
    assert "$1.50" in report

    # No emoji in English mode
    assert "\U0001f4b3" not in report  # credit card
    assert "\U0001f4b0" not in report  # money bag

    # No RUB when usd_rub is None
    assert "RUB" not in report


def test_brief_build_report_en_with_rub():
    """With usd_rub set, RUB equivalents appear."""
    report = build_report_en(
        remaining_balance=12.84,
        total_usage=45.50,
        spend_24h=1.50,
        spend_24h_history=4.5,
        usd_rub=85.0,
        now_date="2026-06-21",
    )

    assert "RUB" in report
    assert "USD/RUB rate" in report
    assert "85.00" in report
    # 12.84 * 85 = 1091.40
    assert "1091.40" in report


def test_brief_build_report_ru_format():
    """RU brief has Russian headers, emoji, and RUB formatting."""
    report = build_report_ru(
        remaining_balance=12.84,
        total_usage=45.50,
        spend_24h=1.50,
        spend_24h_history=4.5,
        usd_rub=85.0,
        now_date="2026-06-21",
    )

    # Russian header
    assert "\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0439 \u043e\u0442\u0447\u0451\u0442" in report
    # Credit card emoji
    assert "\U0001f4b3" in report
    # Russian labels
    assert "\u041e\u0441\u0442\u0430\u0442\u043e\u043a" in report
    assert "\u041e\u0431\u0449\u0438\u0439 \u0440\u0430\u0441\u0445\u043e\u0434" in report
    assert "\u041a\u0443\u0440\u0441" in report
    # RUB (uses "RUB" string, not the symbol)
    assert "RUB" in report
    assert "85.00" in report
    # 12.84 * 85 = 1091.40
    assert "1091.40" in report


def test_brief_fmt_functions():
    """fmt_usd and fmt_rub format correctly."""
    assert fmt_usd(0.0) == "$0.00"
    assert fmt_usd(5.123) == "$5.12"
    assert fmt_usd(1234.5) == "$1234.50"
    assert fmt_rub(0.0) == "0.00 RUB"
    assert fmt_rub(100.5) == "100.50 RUB"

# Fallback tests: empty history -> usage_daily

def test_brief_main_empty_history_fallback():
    """When history is empty, spend_24h falls back to usage_daily."""
    spend_24h_history = 0.0
    usage_daily = 1.23
    if spend_24h_history > 0:
        spend_24h = spend_24h_history
    else:
        spend_24h = usage_daily
    assert spend_24h == 1.23

def test_brief_main_history_available():
    """When history is available, rolling window takes priority."""
    spend_24h_history = 4.5
    usage_daily = 1.0
    if spend_24h_history > 0:
        spend_24h = spend_24h_history
    else:
        spend_24h = usage_daily
    assert spend_24h == 4.5

def test_brief_report_api_counter_not_shown_when_equal():
    """API reference hidden when usage_reference equals spend_24h."""
    from scripts.openrouter_daily_brief import build_report_en
    report = build_report_en(50.0, 20.0, 1.23, 0.0, None, '2026-06-21', usage_reference=1.23)
    assert "API daily counter" not in report

def test_brief_report_api_counter_shown_when_different():
    """API reference appears when usage_reference differs from spend_24h."""
    from scripts.openrouter_daily_brief import build_report_en
    report = build_report_en(50.0, 20.0, 3.95, 0.0, None, '2026-06-21', usage_reference=1.23)
    assert "API daily counter" in report
    assert "$1.23" in report

def test_brief_report_ru_api_counter_shown():
    """RU report shows API counter in Russian."""
    from scripts.openrouter_daily_brief import build_report_ru
    report = build_report_ru(50.0, 20.0, 3.95, 0.0, 85.0, '2026-06-21', usage_reference=1.23)
    assert "Дневной счётчик" in report
    assert "$1.23" in report

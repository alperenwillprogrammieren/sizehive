from datetime import datetime, timedelta, timezone

from app.pricing.history import Snapshot, price_stats

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def snap(days_ago: int, price: int, list_price: int = 10000) -> Snapshot:
    return Snapshot(captured_at=NOW - timedelta(days=days_ago), price_cents=price, list_price_cents=list_price)


def test_empty_history_has_no_stats():
    assert price_stats([], now=NOW) is None


def test_basic_lows_and_highs():
    history = [snap(40, 9000), snap(20, 12000), snap(10, 8000), snap(1, 8500)]
    stats = price_stats(history, now=NOW)

    assert stats.current_cents == 8500
    assert stats.all_time_low_cents == 8000
    assert stats.all_time_high_cents == 12000
    assert stats.snapshot_count == 4
    assert stats.first_seen == NOW - timedelta(days=40)


def test_history_is_sorted_defensively():
    unordered = [snap(1, 8500), snap(40, 9000), snap(10, 8000)]
    stats = price_stats(unordered, now=NOW)
    # "current" must be the newest snapshot, not the last list element.
    assert stats.current_cents == 8500


def test_windowed_lows_respect_their_window():
    history = [snap(100, 5000), snap(60, 6000), snap(20, 7000), snap(2, 7500)]
    stats = price_stats(history, now=NOW)

    assert stats.low_30d_cents == 7000  # only the 20d and 2d points
    assert stats.low_90d_cents == 6000  # excludes the 100d point
    assert stats.all_time_low_cents == 5000


def test_windowed_lows_are_none_when_window_is_empty():
    stats = price_stats([snap(200, 5000)], now=NOW)
    assert stats.low_30d_cents is None
    assert stats.low_90d_cents is None
    assert stats.median_90d_cents is None


def test_is_all_time_low_includes_ties():
    stats = price_stats([snap(10, 8000), snap(1, 8000)], now=NOW)
    assert stats.is_all_time_low is True

    stats = price_stats([snap(10, 7000), snap(1, 8000)], now=NOW)
    assert stats.is_all_time_low is False


def test_days_since_cheaper_finds_most_recent_cheaper_point():
    history = [snap(30, 5000), snap(12, 7000), snap(5, 9000), snap(0, 8000)]
    stats = price_stats(history, now=NOW)
    # 12 days ago it was 7000, which is below the current 8000.
    assert stats.days_since_cheaper == 12


def test_days_since_cheaper_is_none_at_the_cheapest_point_ever():
    history = [snap(30, 9000), snap(10, 9500), snap(0, 8000)]
    assert price_stats(history, now=NOW).days_since_cheaper is None


def test_claimed_discount_uses_the_shops_list_price():
    stats = price_stats([snap(0, 7500, list_price=10000)], now=NOW)
    assert stats.claimed_discount_pct == 25.0


def test_real_discount_uses_the_highest_price_actually_charged():
    # Shop claims 50% off a 10000 list price, but it never sold above 8000.
    history = [snap(20, 8000, list_price=10000), snap(0, 5000, list_price=10000)]
    stats = price_stats(history, now=NOW)

    assert stats.claimed_discount_pct == 50.0
    assert stats.real_discount_pct == 37.5  # 5000 against the real 8000 high
    assert stats.list_price_ever_charged is False


def test_list_price_ever_charged_when_it_really_was():
    history = [snap(20, 10000, list_price=10000), snap(0, 6000, list_price=10000)]
    stats = price_stats(history, now=NOW)

    assert stats.list_price_ever_charged is True
    assert stats.real_discount_pct == 40.0
    assert stats.claimed_discount_pct == 40.0


def test_discounts_are_zero_when_price_is_at_or_above_reference():
    stats = price_stats([snap(10, 5000, list_price=5000), snap(0, 6000, list_price=5000)], now=NOW)
    assert stats.claimed_discount_pct == 0.0
    assert stats.real_discount_pct == 0.0


def test_zero_list_price_does_not_divide_by_zero():
    stats = price_stats([snap(0, 4000, list_price=0)], now=NOW)
    assert stats.claimed_discount_pct == 0.0

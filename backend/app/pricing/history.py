"""Price-history analytics over a variant's snapshot series.

`price_snapshot` is append-only (see CLAUDE.md), so every variant carries a
real, measured price time series. This module turns that series into the
numbers the Deals page and the detail page's price verdict are built on.

The distinction this module exists to make: a shop's *claimed* discount is
`list_price` vs. `price` — a number the shop controls and can inflate. The
*real* discount is the current price against the highest price we ever
actually observed being charged. Everything here is a pure function over
plain snapshots — no ORM, no DB — so those rules stay unit-testable.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median


@dataclass(frozen=True)
class Snapshot:
    captured_at: datetime
    price_cents: int
    list_price_cents: int


@dataclass(frozen=True)
class PriceStats:
    current_cents: int
    all_time_low_cents: int
    all_time_high_cents: int
    low_30d_cents: int | None
    low_90d_cents: int | None
    median_90d_cents: int | None
    is_all_time_low: bool
    #: Days since the price was last *strictly* below what it is now.
    #: None means it has never been cheaper in the recorded history.
    days_since_cheaper: int | None
    #: Did any snapshot ever sell at the advertised list price?
    list_price_ever_charged: bool
    #: What the shop advertises right now: list price vs. current price.
    claimed_discount_pct: float
    #: What we measured: highest price ever actually charged vs. current.
    real_discount_pct: float
    first_seen: datetime
    snapshot_count: int


def _pct_below(reference_cents: int, price_cents: int) -> float:
    """How far `price_cents` sits below `reference_cents`, in percent."""
    if reference_cents <= 0 or price_cents >= reference_cents:
        return 0.0
    return round((reference_cents - price_cents) / reference_cents * 100, 1)


def _low_within(history: list[Snapshot], now: datetime, days: int) -> int | None:
    prices = [s.price_cents for s in history if s.captured_at >= now - timedelta(days=days)]
    return min(prices) if prices else None


def _median_within(history: list[Snapshot], now: datetime, days: int) -> int | None:
    prices = [s.price_cents for s in history if s.captured_at >= now - timedelta(days=days)]
    return round(median(prices)) if prices else None


def _days_since_cheaper(history: list[Snapshot], current: Snapshot) -> int | None:
    """Age of the most recent snapshot that was strictly cheaper than now."""
    for snapshot in reversed(history[:-1]):
        if snapshot.price_cents < current.price_cents:
            return max(0, (current.captured_at - snapshot.captured_at).days)
    return None


def price_stats(history: list[Snapshot], now: datetime | None = None) -> PriceStats | None:
    """Summarise a variant's price series. Returns None for an empty history.

    `history` need not be sorted; `now` defaults to the current time and is
    injectable so the windowed lows are testable against fixed data.
    """
    if not history:
        return None

    history = sorted(history, key=lambda s: s.captured_at)
    current = history[-1]
    now = now or datetime.now(timezone.utc)

    prices = [s.price_cents for s in history]
    all_time_low = min(prices)
    all_time_high = max(prices)

    return PriceStats(
        current_cents=current.price_cents,
        all_time_low_cents=all_time_low,
        all_time_high_cents=all_time_high,
        low_30d_cents=_low_within(history, now, 30),
        low_90d_cents=_low_within(history, now, 90),
        median_90d_cents=_median_within(history, now, 90),
        is_all_time_low=current.price_cents <= all_time_low,
        days_since_cheaper=_days_since_cheaper(history, current),
        list_price_ever_charged=any(s.price_cents == s.list_price_cents for s in history),
        claimed_discount_pct=_pct_below(current.list_price_cents, current.price_cents),
        real_discount_pct=_pct_below(all_time_high, current.price_cents),
        first_seen=history[0].captured_at,
        snapshot_count=len(history),
    )

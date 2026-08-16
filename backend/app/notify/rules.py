"""When does an alert actually fire?

Separated from the DB run (run.py) so the decision — the part that decides
whether a mail goes out — is unit-testable without a database, same as the
normalizers, extractors and price analytics.

Two anti-spam rules are baked in and matter more than the trigger itself:
a repeat notification requires a *strictly lower* price than the one last
reported, and an alert without a target only fires on a price we have never
recorded before.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AlertState:
    current_cents: int
    #: Lowest price ever recorded for this variant, current one included.
    all_time_low_cents: int
    target_cents: int | None
    last_notified_price_cents: int | None
    in_stock: bool


def should_notify(state: AlertState) -> bool:
    if not state.in_stock:
        return False  # nothing to act on

    if state.target_cents is not None:
        if state.current_cents > state.target_cents:
            return False
    elif state.current_cents > state.all_time_low_cents:
        # No target set: only a record low is worth a mail.
        return False

    if state.last_notified_price_cents is None:
        return True
    # Already told them about this article — only a further drop is news.
    return state.current_cents < state.last_notified_price_cents

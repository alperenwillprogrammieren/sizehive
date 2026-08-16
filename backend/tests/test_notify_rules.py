from app.notify.rules import AlertState, should_notify


def state(**overrides):
    base = dict(
        current_cents=5000,
        all_time_low_cents=5000,
        target_cents=None,
        last_notified_price_cents=None,
        in_stock=True,
    )
    base.update(overrides)
    return AlertState(**base)


def test_out_of_stock_never_notifies():
    assert should_notify(state(target_cents=9999, in_stock=False)) is False


# --- with a target price -------------------------------------------------


def test_target_reached_notifies():
    assert should_notify(state(current_cents=4900, target_cents=5000)) is True


def test_target_exactly_hit_notifies():
    assert should_notify(state(current_cents=5000, target_cents=5000)) is True


def test_above_target_stays_quiet():
    assert should_notify(state(current_cents=5100, target_cents=5000)) is False


def test_target_reached_but_already_reported_at_that_price():
    assert should_notify(
        state(current_cents=4900, target_cents=5000, last_notified_price_cents=4900)
    ) is False


def test_target_reached_again_at_a_lower_price_notifies_again():
    assert should_notify(
        state(current_cents=4500, target_cents=5000, last_notified_price_cents=4900)
    ) is True


def test_price_rising_after_a_notification_stays_quiet():
    assert should_notify(
        state(current_cents=4950, target_cents=5000, last_notified_price_cents=4900)
    ) is False


# --- without a target: record lows only ---------------------------------


def test_record_low_notifies_when_no_target_is_set():
    assert should_notify(state(current_cents=4000, all_time_low_cents=4000)) is True


def test_merely_cheap_is_not_enough_without_a_target():
    assert should_notify(state(current_cents=4200, all_time_low_cents=4000)) is False


def test_sitting_at_the_old_record_does_not_notify_twice():
    assert should_notify(
        state(current_cents=4000, all_time_low_cents=4000, last_notified_price_cents=4000)
    ) is False


def test_a_new_deeper_record_notifies_again():
    assert should_notify(
        state(current_cents=3800, all_time_low_cents=3800, last_notified_price_cents=4000)
    ) is True

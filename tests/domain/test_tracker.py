from datetime import datetime, timedelta

import pytest

from activity_tracker.domain.tracker import ActivityPeriod, ActivityTracker

T0 = datetime(2026, 1, 1, 12, 0, 0)
TEN_MIN = timedelta(minutes=10)


def at(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


def test_no_activity_means_nothing_to_report():
    assert ActivityTracker().poll(at(100)) is None


def test_keyboard_and_mouse_then_ten_minutes_idle_gives_period():
    tracker = ActivityTracker(TEN_MIN)
    tracker.keyboard_used(at(0))
    tracker.mouse_used(at(5))

    assert tracker.poll(at(15)) == ActivityPeriod(started_at=at(0), ended_at=at(5))


def test_not_due_before_ten_minutes_of_idle():
    tracker = ActivityTracker(TEN_MIN)
    tracker.keyboard_used(at(0))
    tracker.mouse_used(at(1))

    assert tracker.poll(at(10.9)) is None


def test_any_new_activity_restarts_idle_countdown():
    tracker = ActivityTracker(TEN_MIN)
    tracker.keyboard_used(at(0))
    tracker.mouse_used(at(1))
    tracker.mouse_used(at(9))  # снова что-то потрогали

    assert tracker.poll(at(15)) is None
    assert tracker.poll(at(19)) == ActivityPeriod(at(0), at(9))


@pytest.mark.parametrize("use", ["keyboard_used", "mouse_used"])
def test_only_one_device_never_triggers_and_state_is_reset(use):
    tracker = ActivityTracker(TEN_MIN)
    getattr(tracker, use)(at(0))

    assert tracker.poll(at(20)) is None
    assert tracker.has_activity is False


def test_tracker_resets_after_reporting_a_period():
    tracker = ActivityTracker(TEN_MIN)
    tracker.keyboard_used(at(0))
    tracker.mouse_used(at(0))
    assert tracker.poll(at(10)) is not None

    assert tracker.poll(at(30)) is None

    tracker.keyboard_used(at(40))
    tracker.mouse_used(at(41))
    assert tracker.poll(at(60)) == ActivityPeriod(at(40), at(41))


def test_explicit_reset_forgets_everything():
    tracker = ActivityTracker(TEN_MIN)
    tracker.keyboard_used(at(0))
    tracker.mouse_used(at(0))
    tracker.reset()

    assert tracker.poll(at(60)) is None


def test_idle_threshold_must_be_positive():
    with pytest.raises(ValueError):
        ActivityTracker(timedelta(0))

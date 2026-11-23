from datetime import datetime, timedelta

import pytest

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.errors import ValidationError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.tracker import ActivityPeriod
from activity_tracker.presentation.controller import TrackerController

from ..application.fakes import FakeUnitOfWork
from .fakes import FakeMonitor

NOW = datetime(2026, 11, 23, 18, 0)
PERIOD = ActivityPeriod(NOW - timedelta(minutes=40), NOW - timedelta(minutes=10))


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def service(uow):
    return TrackerService(lambda: uow, clock=lambda: NOW)


def make_controller(service, monitor, ask, after=lambda: None, idle_minutes=10):
    return TrackerController(service, monitor, ask, idle_minutes=idle_minutes, on_recorded=after)


def kinds(uow):
    return [e.kind for e in uow.entries.items]


def test_tick_without_finished_period_does_nothing(service, uow):
    asked = []
    controller = make_controller(service, FakeMonitor(None), lambda *a: asked.append(a) or True)

    controller.tick()

    assert asked == [] and uow.entries.items == []


def test_answer_is_recorded_for_the_detected_period(service, uow):
    def ask(projects, submit, idle_minutes):
        submit("Трекер", "Выполнил", "написал трей")
        return True

    make_controller(service, FakeMonitor(PERIOD), ask).tick()

    entry = uow.entries.items[0]
    assert (entry.kind, entry.comment) == (ActivityKind.DONE, "написал трей")
    assert (entry.started_at, entry.ended_at) == (PERIOD.started_at, PERIOD.ended_at)


def test_closing_the_dialog_records_skipped(service, uow):
    make_controller(service, FakeMonitor(PERIOD), lambda *a: False).tick()

    assert kinds(uow) == [ActivityKind.SKIPPED]


def test_dialog_gets_known_projects_and_idle_minutes(service, uow):
    service.add_manual_entry("Старый", ActivityKind.DONE, "x", PERIOD.started_at, PERIOD.ended_at)
    received = {}

    def ask(projects, submit, idle_minutes):
        received.update(projects=projects, idle=idle_minutes)
        return True

    make_controller(service, FakeMonitor(PERIOD), ask, idle_minutes=7).tick()

    assert received == {"projects": ["Старый"], "idle": 7}


def test_validation_errors_reach_the_dialog_and_nothing_is_saved(service, uow):
    seen = []

    def ask(projects, submit, idle_minutes):
        try:
            submit("", "Изучил", "")
        except ValidationError as exc:
            seen.append(str(exc))
        return True

    make_controller(service, FakeMonitor(PERIOD), ask).tick()

    assert seen and uow.entries.items == []


def test_monitor_is_reset_and_callback_called_after_dialog(service):
    monitor, calls = FakeMonitor(PERIOD), []

    make_controller(service, monitor, lambda *a: True, after=lambda: calls.append("recorded")).tick()

    assert monitor.reset_calls == 1 and calls == ["recorded"]

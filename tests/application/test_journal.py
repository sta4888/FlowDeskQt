from datetime import date, datetime, timedelta

import pytest

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.errors import ValidationError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryFilter

from .fakes import FakeUnitOfWork

NOW = datetime(2026, 11, 23, 18, 0)


def when(day: int, hour: int = 10) -> datetime:
    return datetime(2026, 11, day, hour, 0)


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def service(uow):
    return TrackerService(lambda: uow, clock=lambda: NOW)


@pytest.fixture
def seeded(service):
    service.add_manual_entry("Alembic", ActivityKind.LEARNED, "читал доки", when(20), when(20, 11))
    service.add_manual_entry("Трекер", ActivityKind.DONE, "написал окно", when(22), when(22, 12))
    service.add_manual_entry("", ActivityKind.BROWSING, "", when(23), when(23, 11))
    return service


def test_add_manual_entry_uses_given_period_and_current_time_as_answered_at(service, uow):
    entry_id = service.add_manual_entry("Проект", ActivityKind.DONE, "сделал", when(1), when(1, 12))

    entry = uow.entries.get(entry_id)
    assert (entry.started_at, entry.ended_at, entry.answered_at) == (when(1), when(1, 12), NOW)


def test_add_manual_entry_rejects_reversed_period(service):
    with pytest.raises(ValidationError):
        service.add_manual_entry("Проект", ActivityKind.DONE, "x", when(2), when(1))


def test_search_returns_newest_first_with_project_names(seeded):
    views = seeded.search_entries()

    assert [v.started_at.day for v in views] == [23, 22, 20]
    assert [v.project_name for v in views] == [None, "Трекер", "Alembic"]


def test_search_applies_filter(seeded):
    assert [v.comment for v in seeded.search_entries(EntryFilter(project_name="Трекер"))] == ["написал окно"]
    assert len(seeded.search_entries(EntryFilter(kind=ActivityKind.BROWSING))) == 1
    assert len(seeded.search_entries(EntryFilter(date_from=date(2026, 11, 22)))) == 2
    assert len(seeded.search_entries(EntryFilter(text="ДОКИ"))) == 1


def test_delete_entry_removes_it_and_commits(seeded, uow):
    entry_id = seeded.search_entries()[0].id
    commits_before = uow.commits

    assert seeded.delete_entry(entry_id) is True

    assert entry_id not in [v.id for v in seeded.search_entries()]
    assert uow.commits == commits_before + 1


def test_delete_missing_entry_returns_false_and_does_not_commit(seeded, uow):
    commits_before = uow.commits

    assert seeded.delete_entry(9999) is False
    assert uow.commits == commits_before

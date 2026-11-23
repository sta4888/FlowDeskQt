from datetime import datetime, timedelta

import pytest

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.errors import ValidationError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.tracker import ActivityPeriod

from .fakes import FakeUnitOfWork

NOW = datetime(2026, 1, 1, 12, 0, 0)
PERIOD = ActivityPeriod(started_at=NOW - timedelta(minutes=40), ended_at=NOW - timedelta(minutes=10))


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def service(uow):
    return TrackerService(lambda: uow, clock=lambda: NOW)


def test_record_entry_creates_project_and_entry_and_commits(service, uow):
    entry_id = service.record_entry(PERIOD, ActivityKind.LEARNED, "Alembic", "прочитал туториал")

    project = uow.projects.get_by_name("Alembic")
    entry = uow.entries.get(entry_id)
    assert project is not None and project.created_at == NOW
    assert entry.project_id == project.id
    assert (entry.kind, entry.comment) == (ActivityKind.LEARNED, "прочитал туториал")
    assert (entry.started_at, entry.ended_at, entry.answered_at) == (
        PERIOD.started_at, PERIOD.ended_at, NOW,
    )
    assert uow.commits == 1


def test_existing_project_is_reused_even_with_sloppy_spaces(service, uow):
    service.record_entry(PERIOD, ActivityKind.LEARNED, "Мой проект", "раз")
    service.record_entry(PERIOD, ActivityKind.DONE, "  Мой   проект ", "два")

    assert len(uow.projects.items) == 1
    assert len(uow.entries.items) == 2


@pytest.mark.parametrize("project, comment", [("", "что-то"), ("Проект", "  ")])
def test_work_entry_without_project_or_comment_is_rejected_and_nothing_is_saved(
    service, uow, project, comment
):
    with pytest.raises(ValidationError):
        service.record_entry(PERIOD, ActivityKind.DONE, project, comment)

    assert uow.projects.items == []  # проект не «протёк» в базу
    assert uow.entries.items == []
    assert uow.commits == 0


def test_browsing_does_not_need_project_or_comment(service, uow):
    entry_id = service.record_entry(PERIOD, ActivityKind.BROWSING)

    assert uow.entries.get(entry_id).project_id is None
    assert uow.projects.items == []


def test_record_skipped_saves_skipped_entry(service, uow):
    entry_id = service.record_skipped(PERIOD)

    assert uow.entries.get(entry_id).kind is ActivityKind.SKIPPED


def test_list_projects_puts_recently_used_first(service, uow):
    service.record_entry(PERIOD, ActivityKind.DONE, "Старый", "x")
    later = TrackerService(lambda: uow, clock=lambda: NOW + timedelta(hours=1))
    later.record_entry(PERIOD, ActivityKind.DONE, "Свежий", "y")

    assert service.list_projects() == ["Свежий", "Старый"]

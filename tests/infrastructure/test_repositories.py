from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.model import ActivityEntry, ActivityKind, Project
from activity_tracker.domain.tracker import ActivityPeriod

NOW = datetime(2026, 1, 1, 12, 0, 0)
PERIOD = ActivityPeriod(NOW - timedelta(minutes=40), NOW - timedelta(minutes=10))


def make_entry(project_id, answered_at=NOW, kind=ActivityKind.DONE, comment="сделал"):
    return ActivityEntry(
        kind=kind, comment=comment,
        started_at=PERIOD.started_at, ended_at=PERIOD.ended_at,
        answered_at=answered_at, project_id=project_id,
    )


def test_project_is_saved_with_id_and_found_by_name(uow_factory):
    with uow_factory() as uow:
        project = Project("Alembic", created_at=NOW)
        uow.projects.add(project)
        assert project.id is not None
        uow.commit()

    with uow_factory() as uow:
        found = uow.projects.get_by_name("Alembic")
        assert found.id == project.id and found.created_at == NOW
        assert uow.projects.get_by_name("Нет такого") is None


def test_project_names_are_unique_in_database(uow_factory):
    with uow_factory() as uow:
        uow.projects.add(Project("Дубль", created_at=NOW))
        with pytest.raises(IntegrityError):
            uow.projects.add(Project("Дубль", created_at=NOW))


def test_entry_round_trip_keeps_enum_and_dates(uow_factory):
    with uow_factory() as uow:
        project = Project("P", created_at=NOW)
        uow.projects.add(project)
        entry = make_entry(project.id, kind=ActivityKind.LEARNED, comment="изучил SQLAlchemy")
        uow.entries.add(entry)
        uow.commit()

    with uow_factory() as uow:
        loaded = uow.entries.get(entry.id)
        assert loaded.kind is ActivityKind.LEARNED
        assert loaded.comment == "изучил SQLAlchemy"
        assert (loaded.started_at, loaded.ended_at, loaded.answered_at) == (
            PERIOD.started_at, PERIOD.ended_at, NOW,
        )
        assert [e.id for e in uow.entries.list_for_project(project.id)] == [entry.id]


def test_entry_must_reference_existing_project(uow_factory):
    with uow_factory() as uow:
        with pytest.raises(IntegrityError):
            uow.entries.add(make_entry(project_id=999))


def test_uncommitted_changes_are_rolled_back(uow_factory):
    with uow_factory() as uow:
        uow.projects.add(Project("Призрак", created_at=NOW))

    with uow_factory() as uow:
        assert uow.projects.get_by_name("Призрак") is None


def test_names_by_recent_use_orders_recent_then_unused_alphabetically(uow_factory):
    with uow_factory() as uow:
        old, fresh = Project("Старый", NOW), Project("Свежий", NOW)
        never_b, never_a = Project("Б-без записей", NOW), Project("А-без записей", NOW)
        for p in (old, fresh, never_b, never_a):
            uow.projects.add(p)
        uow.entries.add(make_entry(old.id, answered_at=NOW))
        uow.entries.add(make_entry(fresh.id, answered_at=NOW + timedelta(hours=1)))
        uow.commit()

        assert uow.projects.names_by_recent_use() == [
            "Свежий", "Старый", "А-без записей", "Б-без записей",
        ]


def test_service_end_to_end_on_real_database(uow_factory):
    service = TrackerService(uow_factory, clock=lambda: NOW)

    entry_id = service.record_entry(PERIOD, ActivityKind.DONE, "Трекер", "написал миграции")
    service.record_entry(PERIOD, ActivityKind.BROWSING)

    assert service.list_projects() == ["Трекер"]
    with uow_factory() as uow:
        assert uow.entries.get(entry_id).comment == "написал миграции"

from datetime import date, datetime

import pytest

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryFilter

NOW = datetime(2026, 11, 23, 18, 0)


@pytest.fixture
def service(uow_factory):
    service = TrackerService(uow_factory, clock=lambda: NOW)
    service.add_manual_entry("Alembic", ActivityKind.LEARNED, "Читал документацию",
                             datetime(2026, 11, 20, 10, 0), datetime(2026, 11, 20, 11, 0))
    service.add_manual_entry("Трекер", ActivityKind.DONE, "Написал окно журнала",
                             datetime(2026, 11, 22, 23, 59), datetime(2026, 11, 23, 0, 30))
    service.add_manual_entry("", ActivityKind.BROWSING, "",
                             datetime(2026, 11, 23, 0, 0), datetime(2026, 11, 23, 0, 20))
    return service


def search(uow_factory, **filter_args):
    with uow_factory() as uow:
        return uow.entries.search(EntryFilter(**filter_args))


def test_search_without_filter_returns_all_newest_first_with_project_names(uow_factory, service):
    views = search(uow_factory)

    assert [v.started_at for v in views] == [
        datetime(2026, 11, 23, 0, 0), datetime(2026, 11, 22, 23, 59), datetime(2026, 11, 20, 10, 0),
    ]
    assert [v.project_name for v in views] == [None, "Трекер", "Alembic"]
    assert views[2].kind is ActivityKind.LEARNED


def test_search_by_project_and_kind(uow_factory, service):
    assert [v.project_name for v in search(uow_factory, project_name="Alembic")] == ["Alembic"]
    assert [v.kind for v in search(uow_factory, kind=ActivityKind.BROWSING)] == [ActivityKind.BROWSING]


def test_date_range_includes_whole_last_day_and_excludes_next(uow_factory, service):
    views = search(uow_factory, date_from=date(2026, 11, 22), date_to=date(2026, 11, 22))

    assert [v.started_at for v in views] == [datetime(2026, 11, 22, 23, 59)]


def test_text_search_works_for_cyrillic_in_any_case(uow_factory, service):
    assert [v.project_name for v in search(uow_factory, text="ЖУРНАЛА")] == ["Трекер"]
    assert [v.project_name for v in search(uow_factory, text="алембик")] == []
    assert [v.project_name for v in search(uow_factory, text="alembic")] == ["Alembic"]


def test_delete_removes_row_from_database(uow_factory, service):
    victim = search(uow_factory, project_name="Alembic")[0]

    with uow_factory() as uow:
        assert uow.entries.delete(victim.id) is True
        assert uow.entries.delete(victim.id) is False
        uow.commit()

    assert len(search(uow_factory)) == 2

from datetime import date, datetime, timedelta

import pytest

from activity_tracker.domain.errors import ValidationError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryFilter, EntryView


def view(**overrides) -> EntryView:
    params = dict(
        id=1,
        project_name="Alembic",
        kind=ActivityKind.DONE,
        comment="Написал миграцию",
        started_at=datetime(2026, 11, 23, 14, 30),
        ended_at=datetime(2026, 11, 23, 15, 15),
        answered_at=datetime(2026, 11, 23, 15, 25),
    )
    params.update(overrides)
    return EntryView(**params)


def test_duration_is_time_between_start_and_end():
    assert view().duration == timedelta(minutes=45)


def test_empty_filter_accepts_everything():
    assert EntryFilter().matches(view())
    assert EntryFilter().matches(view(project_name=None))


def test_filter_by_project():
    assert EntryFilter(project_name="Alembic").matches(view())
    assert not EntryFilter(project_name="Другой").matches(view())
    assert not EntryFilter(project_name="Alembic").matches(view(project_name=None))


def test_filter_by_kind():
    assert EntryFilter(kind=ActivityKind.DONE).matches(view())
    assert not EntryFilter(kind=ActivityKind.LEARNED).matches(view())


def test_date_range_is_inclusive_and_uses_start_date():
    day = date(2026, 11, 23)
    assert EntryFilter(date_from=day, date_to=day).matches(view())
    assert not EntryFilter(date_from=day + timedelta(days=1)).matches(view())
    assert not EntryFilter(date_to=day - timedelta(days=1)).matches(view())


def test_date_from_after_date_to_is_invalid():
    with pytest.raises(ValidationError):
        EntryFilter(date_from=date(2026, 11, 24), date_to=date(2026, 11, 23))


@pytest.mark.parametrize("text", ["миграцию", "МИГРАЦИЮ", "  миграц ", "alembic"])
def test_text_search_ignores_case_and_looks_in_comment_and_project(text):
    assert EntryFilter(text=text).matches(view())


def test_text_search_rejects_non_matching():
    assert not EntryFilter(text="docker").matches(view())

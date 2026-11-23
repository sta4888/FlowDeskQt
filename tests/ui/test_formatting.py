from datetime import datetime, timedelta

import pytest

from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryView
from activity_tracker.ui.formatting import format_duration, format_row, summarize


@pytest.mark.parametrize(
    "delta, expected",
    [
        (timedelta(seconds=20), "< 1 мин"),
        (timedelta(minutes=45), "45 мин"),
        (timedelta(minutes=60), "1 ч 00 мин"),
        (timedelta(hours=2, minutes=5), "2 ч 05 мин"),
    ],
)
def test_format_duration(delta, expected):
    assert format_duration(delta) == expected


def make_view(kind=ActivityKind.DONE, minutes=30, project="Трекер", comment="сделал\nокно"):
    start = datetime(2026, 11, 23, 14, 30)
    return EntryView(
        id=1, project_name=project, kind=kind, comment=comment,
        started_at=start, ended_at=start + timedelta(minutes=minutes), answered_at=start,
    )


def test_format_row_is_human_readable_and_single_line():
    assert format_row(make_view()) == (
        "23.11.2026", "14:30–15:00", "30 мин", "Трекер", "Выполнил", "сделал окно",
    )


def test_format_row_shows_dash_when_no_project():
    assert format_row(make_view(project=None, kind=ActivityKind.BROWSING))[3] == "—"


def test_summarize_counts_entries_and_ignores_skipped_in_total_time():
    views = [
        make_view(minutes=30),
        make_view(minutes=45),
        make_view(kind=ActivityKind.SKIPPED, minutes=90),
    ]
    assert summarize(views) == "Записей: 3 · Время: 1 ч 15 мин"


def test_summarize_empty():
    assert summarize([]) == "Записей: 0"

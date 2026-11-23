from datetime import datetime, timedelta

import pytest

from activity_tracker.domain.errors import ValidationError
from activity_tracker.domain.model import ActivityEntry, ActivityKind, Project

NOW = datetime(2026, 1, 1, 12, 0, 0)


def make_entry(**overrides) -> ActivityEntry:
    params = dict(
        kind=ActivityKind.LEARNED,
        comment="читал про Alembic",
        started_at=NOW - timedelta(minutes=30),
        ended_at=NOW - timedelta(minutes=10),
        answered_at=NOW,
        project_id=1,
    )
    params.update(overrides)
    return ActivityEntry(**params)


class TestProject:
    def test_name_is_trimmed_and_inner_spaces_collapsed(self):
        assert Project(name="  Мой   проект ", created_at=NOW).name == "Мой проект"

    @pytest.mark.parametrize("name", ["", "   ", None])
    def test_empty_name_is_rejected(self, name):
        with pytest.raises(ValidationError):
            Project(name=name, created_at=NOW)

    def test_too_long_name_is_rejected(self):
        with pytest.raises(ValidationError):
            Project(name="x" * 101, created_at=NOW)


class TestActivityEntry:
    @pytest.mark.parametrize("kind", [ActivityKind.LEARNED, ActivityKind.DONE])
    def test_work_entry_requires_project(self, kind):
        with pytest.raises(ValidationError):
            make_entry(kind=kind, project_id=None)

    @pytest.mark.parametrize("kind", [ActivityKind.LEARNED, ActivityKind.DONE])
    @pytest.mark.parametrize("comment", ["", "   "])
    def test_work_entry_requires_comment(self, kind, comment):
        with pytest.raises(ValidationError):
            make_entry(kind=kind, comment=comment)

    @pytest.mark.parametrize("kind", [ActivityKind.BROWSING, ActivityKind.SKIPPED])
    def test_browsing_and_skipped_need_neither_project_nor_comment(self, kind):
        entry = make_entry(kind=kind, project_id=None, comment="")
        assert entry.project_id is None

    def test_comment_is_trimmed(self):
        assert make_entry(comment="  привет \n").comment == "привет"

    def test_period_cannot_end_before_it_starts(self):
        with pytest.raises(ValidationError):
            make_entry(started_at=NOW, ended_at=NOW - timedelta(seconds=1))

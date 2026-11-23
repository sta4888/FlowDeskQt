"""Сценарии использования. Знают о портах, но не о SQLAlchemy и не о Tk."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from activity_tracker.domain.model import ActivityEntry, ActivityKind, Project
from activity_tracker.domain.queries import EntryFilter, EntryView
from activity_tracker.domain.tracker import ActivityPeriod

from .unit_of_work import UnitOfWork


class TrackerService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def list_projects(self) -> list[str]:
        with self._uow_factory() as uow:
            return uow.projects.names_by_recent_use()

    def record_entry(
        self,
        period: ActivityPeriod,
        kind: ActivityKind,
        project_name: str = "",
        comment: str = "",
    ) -> int:
        """Сохраняет ответ пользователя. Бросает ValidationError, если ответ неполный
        (тогда в базе не остаётся ничего, в том числе нового проекта)."""
        now = self._clock()
        with self._uow_factory() as uow:
            project_id = None
            if project_name.strip():
                name = Project.normalize_name(project_name)
                project = uow.projects.get_by_name(name)
                if project is None:
                    project = Project(name=name, created_at=now)
                    uow.projects.add(project)
                project_id = project.id

            entry = ActivityEntry(
                kind=kind,
                comment=comment,
                started_at=period.started_at,
                ended_at=period.ended_at,
                answered_at=now,
                project_id=project_id,
            )
            uow.entries.add(entry)
            uow.commit()
            return entry.id

    def record_skipped(self, period: ActivityPeriod) -> int:
        return self.record_entry(period, ActivityKind.SKIPPED)

    def add_manual_entry(
        self,
        project_name: str,
        kind: ActivityKind,
        comment: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> int:
        """Запись, добавленная вручную (например, задним числом)."""
        return self.record_entry(ActivityPeriod(started_at, ended_at), kind, project_name, comment)

    def search_entries(self, criteria: EntryFilter = EntryFilter()) -> list[EntryView]:
        with self._uow_factory() as uow:
            return uow.entries.search(criteria)

    def delete_entry(self, entry_id: int) -> bool:
        with self._uow_factory() as uow:
            deleted = uow.entries.delete(entry_id)
            if deleted:
                uow.commit()
            return deleted

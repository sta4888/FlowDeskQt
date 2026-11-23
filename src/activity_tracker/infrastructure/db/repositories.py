from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from activity_tracker.domain.model import ActivityEntry, Project
from activity_tracker.domain.queries import EntryFilter, EntryView
from activity_tracker.domain.repositories import EntryRepository, ProjectRepository


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        self._session.add(project)
        self._session.flush()  # присваивает id

    def get_by_name(self, name: str) -> Optional[Project]:
        return self._session.scalar(select(Project).where(Project.name == name))

    def names_by_recent_use(self) -> list[str]:
        last_used = func.max(ActivityEntry.answered_at)
        stmt = (
            select(Project.name)
            .outerjoin(ActivityEntry, ActivityEntry.project_id == Project.id)
            .group_by(Project.id, Project.name)
            .order_by(last_used.is_(None), last_used.desc(), Project.name)
        )
        return list(self._session.scalars(stmt))


class SqlAlchemyEntryRepository(EntryRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: ActivityEntry) -> None:
        self._session.add(entry)
        self._session.flush()  # присваивает id

    def get(self, entry_id: int) -> Optional[ActivityEntry]:
        return self._session.get(ActivityEntry, entry_id)

    def list_for_project(self, project_id: int) -> list[ActivityEntry]:
        stmt = (
            select(ActivityEntry)
            .where(ActivityEntry.project_id == project_id)
            .order_by(ActivityEntry.started_at)
        )
        return list(self._session.scalars(stmt))

    def search(self, criteria: EntryFilter) -> list[EntryView]:
        stmt = (
            select(ActivityEntry, Project.name)
            .outerjoin(Project, ActivityEntry.project_id == Project.id)
            .order_by(ActivityEntry.started_at.desc(), ActivityEntry.id.desc())
        )
        if criteria.project_name is not None:
            stmt = stmt.where(Project.name == criteria.project_name)
        if criteria.kind is not None:
            stmt = stmt.where(ActivityEntry.kind == criteria.kind)
        if criteria.date_from is not None:
            stmt = stmt.where(ActivityEntry.started_at >= datetime.combine(criteria.date_from, time.min))
        if criteria.date_to is not None:
            next_day = datetime.combine(criteria.date_to + timedelta(days=1), time.min)
            stmt = stmt.where(ActivityEntry.started_at < next_day)

        views = [
            EntryView(
                id=entry.id,
                project_name=project_name,
                kind=entry.kind,
                comment=entry.comment,
                started_at=entry.started_at,
                ended_at=entry.ended_at,
                answered_at=entry.answered_at,
            )
            for entry, project_name in self._session.execute(stmt)
        ]
        # Регистронезависимый поиск по кириллице в SQLite (LIKE/lower) не работает,
        # поэтому текстовый фильтр применяется в Python.
        return [view for view in views if criteria.accepts_text(view)]

    def delete(self, entry_id: int) -> bool:
        entry = self._session.get(ActivityEntry, entry_id)
        if entry is None:
            return False
        self._session.delete(entry)
        self._session.flush()
        return True

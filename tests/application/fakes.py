"""In-memory реализации портов для быстрых тестов без БД."""

from __future__ import annotations

from typing import Optional

from activity_tracker.application.unit_of_work import UnitOfWork
from activity_tracker.domain.model import ActivityEntry, Project
from activity_tracker.domain.queries import EntryFilter, EntryView
from activity_tracker.domain.repositories import EntryRepository, ProjectRepository


class FakeEntryRepository(EntryRepository):
    def __init__(self) -> None:
        self.items: list[ActivityEntry] = []

    def add(self, entry: ActivityEntry) -> None:
        entry.id = len(self.items) + 1
        self.items.append(entry)

    def get(self, entry_id: int) -> Optional[ActivityEntry]:
        return next((e for e in self.items if e.id == entry_id), None)

    def list_for_project(self, project_id: int) -> list[ActivityEntry]:
        return [e for e in self.items if e.project_id == project_id]

    def search(self, criteria: EntryFilter) -> list[EntryView]:
        names = {p.id: p.name for p in self.projects.items}
        views = [
            EntryView(
                id=e.id, project_name=names.get(e.project_id), kind=e.kind, comment=e.comment,
                started_at=e.started_at, ended_at=e.ended_at, answered_at=e.answered_at,
            )
            for e in self.items
        ]
        matching = [v for v in views if criteria.matches(v)]
        return sorted(matching, key=lambda v: (v.started_at, v.id), reverse=True)

    def delete(self, entry_id: int) -> bool:
        entry = self.get(entry_id)
        if entry is None:
            return False
        self.items.remove(entry)
        return True


class FakeProjectRepository(ProjectRepository):
    def __init__(self, entries: FakeEntryRepository) -> None:
        self.items: list[Project] = []
        self._entries = entries

    def add(self, project: Project) -> None:
        project.id = len(self.items) + 1
        self.items.append(project)

    def get_by_name(self, name: str) -> Optional[Project]:
        return next((p for p in self.items if p.name == name), None)

    def names_by_recent_use(self) -> list[str]:
        # недавно использованные первыми, неиспользованные в конце по алфавиту
        used = sorted(
            (p for p in self.items if any(e.project_id == p.id for e in self._entries.items)),
            key=lambda p: max(e.answered_at for e in self._entries.items if e.project_id == p.id),
            reverse=True,
        )
        unused = sorted(
            (p for p in self.items if p not in used), key=lambda p: p.name
        )
        return [p.name for p in used + unused]


class FakeUnitOfWork(UnitOfWork):
    """Один экземпляр переживает несколько `with`, чтобы тест видел итоговое состояние."""

    def __init__(self) -> None:
        self.entries = FakeEntryRepository()
        self.projects = FakeProjectRepository(self.entries)
        self.entries.projects = self.projects
        self.commits = 0

    def __enter__(self) -> "FakeUnitOfWork":
        self._snapshot = (list(self.projects.items), list(self.entries.items))
        return self

    def commit(self) -> None:
        self.commits += 1
        self._snapshot = (list(self.projects.items), list(self.entries.items))

    def rollback(self) -> None:
        self.projects.items, self.entries.items = (list(s) for s in self._snapshot)

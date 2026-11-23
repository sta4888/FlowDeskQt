from __future__ import annotations

from abc import ABC, abstractmethod

from activity_tracker.domain.repositories import EntryRepository, ProjectRepository


class UnitOfWork(ABC):
    """Одна бизнес-транзакция. Выход из `with` без commit() откатывает изменения."""

    projects: ProjectRepository
    entries: EntryRepository

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, *exc_info) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

"""Порты (интерфейсы) хранилищ. Реализации лежат в infrastructure."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .model import ActivityEntry, Project
from .queries import EntryFilter, EntryView


class ProjectRepository(ABC):
    @abstractmethod
    def add(self, project: Project) -> None:
        """Сохраняет проект и сразу присваивает ему id."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Project]: ...

    @abstractmethod
    def names_by_recent_use(self) -> list[str]:
        """Имена проектов: сначала недавно использованные, потом остальные по алфавиту."""


class EntryRepository(ABC):
    @abstractmethod
    def add(self, entry: ActivityEntry) -> None:
        """Сохраняет запись и сразу присваивает ей id."""

    @abstractmethod
    def get(self, entry_id: int) -> Optional[ActivityEntry]: ...

    @abstractmethod
    def list_for_project(self, project_id: int) -> list[ActivityEntry]: ...

    @abstractmethod
    def search(self, criteria: EntryFilter) -> list[EntryView]:
        """Записи по фильтру, новые (по началу активности) первыми."""

    @abstractmethod
    def delete(self, entry_id: int) -> bool:
        """True, если запись существовала и удалена."""

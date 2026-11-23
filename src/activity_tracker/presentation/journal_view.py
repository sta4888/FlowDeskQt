"""Контракт между презентером и конкретным UI-тулкитом (Tk, Qt, ...)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Sequence

from .formatting import KIND_LABELS

ALL = "Все"
KIND_FILTER_CHOICES = (ALL, *KIND_LABELS.values())


@dataclass(frozen=True)
class FilterInput:
    """Сырые значения полей фильтра, как их ввёл пользователь."""

    project: str = ALL
    kind: str = ALL
    date_from: str = ""
    date_to: str = ""
    text: str = ""


@dataclass(frozen=True)
class JournalRow:
    id: int
    cells: tuple[str, ...]  # дата, время, длительность, проект, тип, комментарий
    comment: str            # полный комментарий для панели деталей


@dataclass(frozen=True)
class NewEntryDefaults:
    project: str
    kind_label: str
    kind_labels: tuple[str, ...]
    start_text: str
    end_text: str


# project, kind_label, comment, start_text, end_text -> сохраняет или бросает DomainError
NewEntrySubmit = Callable[[str, str, str, str, str], object]


class JournalView(ABC):
    """Пассивное представление: только показывает то, что скажет презентер."""

    @abstractmethod
    def show_rows(self, rows: Sequence[JournalRow]) -> None: ...

    @abstractmethod
    def show_status(self, text: str, is_error: bool) -> None: ...

    @abstractmethod
    def show_details(self, comment: str) -> None: ...

    @abstractmethod
    def set_project_choices(self, choices: list[str]) -> None: ...

    @abstractmethod
    def set_filter_inputs(self, inputs: FilterInput) -> None:
        """Программно меняет поля фильтра (пресеты, сброс)."""

    @abstractmethod
    def confirm_delete(self) -> bool: ...

    @abstractmethod
    def ask_new_entry(
        self, projects: list[str], defaults: NewEntryDefaults, submit: NewEntrySubmit
    ) -> bool:
        """Модальная форма. Вызывает submit при сохранении (он может бросить DomainError,
        тогда форму нужно оставить открытой и показать текст ошибки).
        True, если запись сохранена."""

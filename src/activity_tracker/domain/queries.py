"""Модель чтения: фильтр и представление записи для журнала."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from .errors import ValidationError
from .model import ActivityKind


@dataclass(frozen=True)
class EntryView:
    """Запись вместе с названием проекта (то, что показывает журнал)."""

    id: int
    project_name: Optional[str]
    kind: ActivityKind
    comment: str
    started_at: datetime
    ended_at: datetime
    answered_at: datetime

    @property
    def duration(self) -> timedelta:
        return self.ended_at - self.started_at


@dataclass(frozen=True)
class EntryFilter:
    project_name: Optional[str] = None
    kind: Optional[ActivityKind] = None
    date_from: Optional[date] = None  # по дате начала активности, включительно
    date_to: Optional[date] = None    # включительно
    text: str = ""                    # ищет в комментарии и названии проекта, без учёта регистра

    def __post_init__(self) -> None:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError("Дата «С» позже даты «По»")

    def accepts_text(self, view: EntryView) -> bool:
        needle = self.text.strip().casefold()
        if not needle:
            return True
        return needle in f"{view.comment} {view.project_name or ''}".casefold()

    def matches(self, view: EntryView) -> bool:
        if self.project_name is not None and view.project_name != self.project_name:
            return False
        if self.kind is not None and view.kind is not self.kind:
            return False
        day = view.started_at.date()
        if self.date_from and day < self.date_from:
            return False
        if self.date_to and day > self.date_to:
            return False
        return self.accepts_text(view)

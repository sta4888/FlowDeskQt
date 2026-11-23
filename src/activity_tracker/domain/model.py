"""Сущности предметной области. Никаких зависимостей от БД, UI и фреймворков."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .errors import ValidationError

MAX_PROJECT_NAME_LENGTH = 100


class ActivityKind(str, Enum):
    LEARNED = "learned"    # изучил что-то
    DONE = "done"          # выполнил что-то
    BROWSING = "browsing"  # просто гуглил
    SKIPPED = "skipped"    # закрыл окно, не ответив

    @property
    def requires_details(self) -> bool:
        """Для «работы» обязательны проект и комментарий."""
        return self in (ActivityKind.LEARNED, ActivityKind.DONE)


@dataclass(eq=False)
class Project:
    name: str
    created_at: datetime
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.name = self.normalize_name(self.name)

    @staticmethod
    def normalize_name(name: Optional[str]) -> str:
        normalized = " ".join((name or "").split())
        if not normalized:
            raise ValidationError("Выбери или впиши проект")
        if len(normalized) > MAX_PROJECT_NAME_LENGTH:
            raise ValidationError(
                f"Название проекта длиннее {MAX_PROJECT_NAME_LENGTH} символов"
            )
        return normalized


@dataclass(eq=False)
class ActivityEntry:
    """Запись о том, чем ты занимался в период активности.

    На проект ссылается по id: это отдельный агрегат.
    """

    kind: ActivityKind
    comment: str
    started_at: datetime
    ended_at: datetime
    answered_at: datetime
    project_id: Optional[int] = None
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.comment = (self.comment or "").strip()
        if self.ended_at < self.started_at:
            raise ValidationError("Конец активности раньше её начала")
        if self.kind.requires_details:
            if self.project_id is None:
                raise ValidationError("Выбери или впиши проект")
            if not self.comment:
                raise ValidationError("Напиши, что именно ты изучил или сделал")

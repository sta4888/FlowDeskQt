"""Порты внешних источников событий."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from activity_tracker.domain.tracker import ActivityPeriod


class ActivityMonitor(ABC):
    """Источник событий активности (клавиатура/мышь)."""

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def poll(self) -> Optional[ActivityPeriod]:
        """Вернёт период, если пора спрашивать пользователя."""

    @abstractmethod
    def reset(self) -> None: ...

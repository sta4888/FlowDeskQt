"""Логика «когда пора спросить пользователя». Чистая, время передаётся снаружи."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass(frozen=True)
class ActivityPeriod:
    started_at: datetime  # первое действие
    ended_at: datetime    # последнее действие перед паузой


class ActivityTracker:
    """Окно нужно показать, когда:
    1) за период использовались И клавиатура, И мышь;
    2) после последнего действия прошло `idle_threshold` без какого-либо ввода.
    """

    def __init__(self, idle_threshold: timedelta = timedelta(minutes=10)) -> None:
        if idle_threshold <= timedelta(0):
            raise ValueError("idle_threshold должен быть положительным")
        self._idle_threshold = idle_threshold
        self.reset()

    def reset(self) -> None:
        self._first: Optional[datetime] = None
        self._last: Optional[datetime] = None
        self._keyboard = False
        self._mouse = False

    @property
    def has_activity(self) -> bool:
        return self._last is not None

    def keyboard_used(self, at: datetime) -> None:
        self._keyboard = True
        self._touch(at)

    def mouse_used(self, at: datetime) -> None:
        self._mouse = True
        self._touch(at)

    def _touch(self, at: datetime) -> None:
        if self._first is None:
            self._first = at
        self._last = at

    def poll(self, now: datetime) -> Optional[ActivityPeriod]:
        """Вернёт период, если пора спрашивать. После паузы состояние всегда
        сбрасывается, даже если использовалось только одно устройство."""
        if self._last is None or now - self._last < self._idle_threshold:
            return None
        period = None
        if self._keyboard and self._mouse:
            period = ActivityPeriod(self._first, self._last)
        self.reset()
        return period

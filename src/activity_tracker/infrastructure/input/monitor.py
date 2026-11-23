"""Адаптер pynput: слушает ввод и передаёт в доменный ActivityTracker.

Сами нажатые клавиши игнорируются, фиксируется только факт активности.
Слушатели pynput работают в своих потоках, поэтому доступ к трекеру под замком.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Callable, Optional

from activity_tracker.domain.tracker import ActivityPeriod, ActivityTracker


class PynputInputMonitor:
    def __init__(
        self,
        tracker: ActivityTracker,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._tracker = tracker
        self._clock = clock
        self._lock = threading.Lock()
        self._listeners: list = []

    def start(self) -> None:
        from pynput import keyboard, mouse  # импорт здесь, чтобы тесты не требовали pynput

        self._listeners = [
            keyboard.Listener(on_press=self._on_key),
            mouse.Listener(
                on_move=self._on_mouse, on_click=self._on_mouse, on_scroll=self._on_mouse
            ),
        ]
        for listener in self._listeners:
            listener.start()

    def stop(self) -> None:
        for listener in self._listeners:
            listener.stop()

    def poll(self) -> Optional[ActivityPeriod]:
        with self._lock:
            return self._tracker.poll(self._clock())

    def reset(self) -> None:
        with self._lock:
            self._tracker.reset()

    def _on_key(self, _key) -> None:
        with self._lock:
            self._tracker.keyboard_used(self._clock())

    def _on_mouse(self, *_args) -> None:
        with self._lock:
            self._tracker.mouse_used(self._clock())

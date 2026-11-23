from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable


class TrayIcon(ABC):
    """Значок в области уведомлений. Колбэки вызываются из ЧУЖОГО потока:
    их нужно перекинуть в главный поток UI (например, через очередь)."""

    @abstractmethod
    def start(self, on_open: Callable[[], None], on_quit: Callable[[], None]) -> bool:
        """False, если трей недоступен (тогда приложение сворачивает окно обычным способом)."""

    @abstractmethod
    def notify(self, message: str) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

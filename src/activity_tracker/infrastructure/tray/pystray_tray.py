"""Адаптер трея на pystray. Работает в своём потоке (run_detached)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from activity_tracker.presentation.ports import TrayIcon

log = logging.getLogger(__name__)
TITLE = "Activity Tracker"


class PystrayTrayIcon(TrayIcon):
    def __init__(self, image_path: Path) -> None:
        self._image_path = image_path
        self._icon: Optional[object] = None

    def start(self, on_open: Callable[[], None], on_quit: Callable[[], None]) -> bool:
        try:
            import pystray  # импорт здесь: без трея приложение всё равно должно работать
            from PIL import Image

            menu = pystray.Menu(
                # default=True: действие по клику на сам значок
                pystray.MenuItem("Открыть журнал", lambda _icon, _item: on_open(), default=True),
                pystray.MenuItem("Выход", lambda _icon, _item: on_quit()),
            )
            self._icon = pystray.Icon("activity-tracker", Image.open(self._image_path), TITLE, menu)
            self._icon.run_detached()
            return True
        except Exception:
            log.exception("Не удалось создать значок в трее")
            self._icon = None
            return False

    def notify(self, message: str) -> None:
        if self._icon is None:
            return
        try:
            self._icon.notify(message, TITLE)
        except Exception:  # уведомления не критичны (на некоторых платформах не поддерживаются)
            log.debug("Уведомление не показано", exc_info=True)

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                log.debug("Ошибка при остановке трея", exc_info=True)
            self._icon = None

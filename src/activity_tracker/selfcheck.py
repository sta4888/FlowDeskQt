"""Быстрая проверка, что программа (в том числе собранный exe) цела.

    ActivityTracker.exe --self-check      # код выхода 0 = всё в порядке

Не открывает окон и не слушает ввод: проверяет миграции, работу с БД, иконки и,
на Windows, наличие GUI-библиотек внутри сборки.
"""

from __future__ import annotations

import logging
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from activity_tracker.resources import asset_path

log = logging.getLogger(__name__)
ASSETS = ("app.ico", "app.png", "tray.png")


def run(check_gui_libs: bool = sys.platform == "win32") -> int:
    try:
        _check_database()
        _check_assets()
        if check_gui_libs:
            _check_gui_libs()
    except Exception:
        log.exception("self-check не пройден")
        print("SELF-CHECK FAILED", file=sys.stderr)
        return 1
    print("SELF-CHECK OK")
    return 0


def _check_database() -> None:
    from activity_tracker.application.services import TrackerService
    from activity_tracker.domain.model import ActivityKind
    from activity_tracker.infrastructure.db.database import (
        make_engine, make_session_factory, upgrade_to_head,
    )
    from activity_tracker.infrastructure.db.orm import start_mappers
    from activity_tracker.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork

    with tempfile.TemporaryDirectory() as tmp:
        url = f"sqlite:///{Path(tmp) / 'selfcheck.db'}"
        upgrade_to_head(url)  # доказывает, что миграции лежат там, где их ищет Alembic
        start_mappers()
        engine = make_engine(url)
        try:
            service = TrackerService(lambda: SqlAlchemyUnitOfWork(make_session_factory(engine)))
            now = datetime.now()
            service.add_manual_entry("self-check", ActivityKind.DONE, "ok", now - timedelta(hours=1), now)
            assert len(service.search_entries()) == 1
        finally:
            engine.dispose()


def _check_assets() -> None:
    missing = [name for name in ASSETS if not asset_path(name).is_file()]
    if missing:
        raise FileNotFoundError(f"нет файлов иконок: {missing}")


def _check_gui_libs() -> None:
    import PIL.Image  # noqa: F401
    import pystray  # noqa: F401
    from pynput import keyboard, mouse  # noqa: F401

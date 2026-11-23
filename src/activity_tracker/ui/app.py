"""Composition root: здесь всё собирается воедино."""

from __future__ import annotations

import argparse
import os
import tkinter as tk
from datetime import timedelta
from typing import Optional, Sequence

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.tracker import ActivityTracker
from activity_tracker.infrastructure.db.database import (
    default_db_url,
    make_engine,
    make_session_factory,
    upgrade_to_head,
)
from activity_tracker.infrastructure.db.orm import start_mappers
from activity_tracker.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from activity_tracker.infrastructure.input.monitor import PynputInputMonitor

from .dialog import ask_user
from .journal import JournalWindow

IDLE_SECONDS_ENV = "ACTIVITY_TRACKER_IDLE_SECONDS"  # для быстрой проверки, например 10


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="activity-tracker")
    parser.add_argument("--minimized", action="store_true", help="запустить со свёрнутым журналом")
    args = parser.parse_args(argv)

    idle_seconds = int(os.environ.get(IDLE_SECONDS_ENV, 10))
    url = default_db_url()

    upgrade_to_head(url)  # применяет недостающие миграции
    start_mappers()
    session_factory = make_session_factory(make_engine(url))
    service = TrackerService(lambda: SqlAlchemyUnitOfWork(session_factory))

    monitor = PynputInputMonitor(ActivityTracker(timedelta(seconds=idle_seconds)))
    monitor.start()

    root = tk.Tk()
    journal = JournalWindow(root, service, on_quit=root.destroy)
    # Крестик не завершает трекер, а сворачивает окно. Выход: кнопка «Выйти из трекера».
    root.protocol("WM_DELETE_WINDOW", root.iconify)
    if args.minimized:
        root.iconify()

    def check() -> None:
        period = monitor.poll()
        if period is not None:
            answered = ask_user(
                root,
                service.list_projects(),
                lambda project, kind, comment: service.record_entry(period, kind, project, comment),
                idle_minutes=max(1, idle_seconds // 60),
            )
            if not answered:
                service.record_skipped(period)
            monitor.reset()  # ввод во время ответа не считается новой активностью
            journal.refresh_projects()
            journal.refresh()
        root.after(1000, check)

    root.after(1000, check)
    print(f"Трекер запущен. БД: {url}\nВыход: кнопка «Выйти из трекера» или Ctrl+C")
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()

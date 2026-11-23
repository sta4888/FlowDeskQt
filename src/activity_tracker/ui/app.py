"""Composition root для Tk: здесь всё собирается воедино."""

from __future__ import annotations

import argparse
import logging
import os
import queue
import sys
import tkinter as tk
from datetime import timedelta
from typing import Optional, Sequence

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.tracker import ActivityTracker
from activity_tracker.infrastructure.db.database import (
    default_db_url, make_engine, make_session_factory, upgrade_to_head,
)
from activity_tracker.infrastructure.db.orm import start_mappers
from activity_tracker.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from activity_tracker.infrastructure.input.monitor import PynputInputMonitor
from activity_tracker.infrastructure.logging_setup import configure_logging
from activity_tracker.infrastructure.tray.pystray_tray import PystrayTrayIcon
from activity_tracker.presentation.controller import TrackerController
from activity_tracker.presentation.journal_presenter import JournalPresenter
from activity_tracker.resources import asset_path

from .dialog import ask_question
from .tk_journal import TkJournalView

log = logging.getLogger(__name__)
IDLE_SECONDS_ENV = "ACTIVITY_TRACKER_IDLE_SECONDS"  # для быстрой проверки, например 10
APP_ID = "ActivityTracker.App"


def _set_windows_app_id() -> None:
    """Чтобы на панели задач Windows была наша иконка, а не иконка Python."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            log.debug("AppUserModelID не установлен", exc_info=True)


def _set_window_icon(root: tk.Tk) -> None:
    try:
        root._icon_image = tk.PhotoImage(file=str(asset_path("app.png")))  # ссылка, чтобы не собрал GC
        root.iconphoto(True, root._icon_image)  # type: ignore[attr-defined]
    except Exception:
        log.warning("Не удалось установить иконку окна", exc_info=True)


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="activity-tracker")
    parser.add_argument("--minimized", action="store_true", help="запустить, спрятав журнал в трей")
    args = parser.parse_args(argv)

    configure_logging()
    _set_windows_app_id()

    idle_seconds = int(os.environ.get(IDLE_SECONDS_ENV, 10))
    url = default_db_url()
    log.info("Старт. БД: %s", url)

    upgrade_to_head(url)  # применяет недостающие миграции
    start_mappers()
    session_factory = make_session_factory(make_engine(url))
    service = TrackerService(lambda: SqlAlchemyUnitOfWork(session_factory))

    monitor = PynputInputMonitor(ActivityTracker(timedelta(seconds=idle_seconds)))
    monitor.start()

    root = tk.Tk()
    root.report_callback_exception = lambda exc, val, tb: log.error(
        "Ошибка в обработчике Tk", exc_info=(exc, val, tb)
    )
    _set_window_icon(root)

    # ----- журнал: view + presenter -----
    def quit_app() -> None:
        log.info("Выход")
        monitor.stop()
        tray.stop()
        root.destroy()

    view = TkJournalView(root, on_quit=quit_app)
    presenter = JournalPresenter(service, view)
    view.attach(presenter)
    presenter.start()

    # ----- трей: сворачивается только окно журнала -----
    commands: "queue.Queue[str]" = queue.Queue()  # трей живёт в другом потоке
    tray = PystrayTrayIcon(asset_path("tray.png"))
    tray_ok = tray.start(on_open=lambda: commands.put("open"), on_quit=lambda: commands.put("quit"))
    notified = {"value": False}

    def hide_window() -> None:
        if not tray_ok:
            root.iconify()  # трея нет: хотя бы сворачиваем на панель задач
            return
        root.withdraw()
        if not notified["value"]:
            notified["value"] = True
            tray.notify("Журнал свёрнут в трей, трекер продолжает работать.")

    def show_window() -> None:
        presenter.refresh_projects()
        presenter.refresh()
        root.deiconify()
        root.lift()
        root.focus_force()

    def on_unmap(event: tk.Event) -> None:
        # кнопка «свернуть» тоже прячет окно в трей
        if event.widget is root and tray_ok and root.state() == "iconic":
            hide_window()

    root.protocol("WM_DELETE_WINDOW", hide_window)  # крестик = в трей, а не выход
    root.bind("<Unmap>", on_unmap)

    def pump_commands() -> None:
        while True:
            try:
                command = commands.get_nowait()
            except queue.Empty:
                break
            if command == "open":
                show_window()
            elif command == "quit":
                quit_app()
                return
        root.after(200, pump_commands)

    # ----- вопрос после паузы: отдельное окно, в трей не прячется -----
    controller = TrackerController(
        service,
        monitor,
        ask_question=lambda projects, submit, idle: ask_question(root, projects, submit, idle),
        idle_minutes=max(1, idle_seconds // 60),
        on_recorded=lambda: (presenter.refresh_projects(), presenter.refresh()),
    )

    def tick() -> None:
        try:
            controller.tick()
        except Exception:
            log.exception("Ошибка в цикле трекера")
        root.after(1000, tick)

    root.after(200, pump_commands)
    root.after(1000, tick)
    if args.minimized:
        hide_window()

    print(f"Трекер запущен. БД: {url}\nВыход: «Выйти из трекера», пункт «Выход» в трее или Ctrl+C")
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()
        tray.stop()

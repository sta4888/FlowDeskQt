"""Форма ручного добавления записи."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk
from typing import Callable

from activity_tracker.domain.errors import DomainError
from activity_tracker.domain.model import ActivityKind

from .formatting import KIND_LABELS
from .parsing import DISPLAY_DATETIME_FORMAT

FORM_KINDS = [ActivityKind.LEARNED, ActivityKind.DONE, ActivityKind.BROWSING]

# project_name, kind, comment, started_text, ended_text -> сохраняет или бросает DomainError
SubmitFn = Callable[[str, ActivityKind, str, str, str], object]


def open_entry_form(root: tk.Misc, projects: list[str], submit: SubmitFn) -> bool:
    """Модальная форма. True, если запись сохранена."""
    saved = {"value": False}
    kind_by_label = {KIND_LABELS[k]: k for k in FORM_KINDS}

    win = tk.Toplevel(root)
    win.title("Новая запись")
    win.resizable(False, False)

    frame = ttk.Frame(win, padding=15)
    frame.grid()

    ttk.Label(frame, text="Проект:").grid(row=0, column=0, sticky="w", pady=3)
    project_box = ttk.Combobox(frame, values=projects, width=42)
    project_box.grid(row=0, column=1, sticky="w", pady=3)
    if projects:
        project_box.set(projects[0])

    ttk.Label(frame, text="Что это было:").grid(row=1, column=0, sticky="w", pady=3)
    kind_box = ttk.Combobox(frame, values=list(kind_by_label), state="readonly", width=20)
    kind_box.grid(row=1, column=1, sticky="w", pady=3)
    kind_box.set(KIND_LABELS[ActivityKind.LEARNED])

    now = datetime.now().replace(second=0, microsecond=0)
    ttk.Label(frame, text="Начало:").grid(row=2, column=0, sticky="w", pady=3)
    start_entry = ttk.Entry(frame, width=20)
    start_entry.grid(row=2, column=1, sticky="w", pady=3)
    start_entry.insert(0, (now - timedelta(minutes=30)).strftime(DISPLAY_DATETIME_FORMAT))

    ttk.Label(frame, text="Конец:").grid(row=3, column=0, sticky="w", pady=3)
    end_entry = ttk.Entry(frame, width=20)
    end_entry.grid(row=3, column=1, sticky="w", pady=3)
    end_entry.insert(0, now.strftime(DISPLAY_DATETIME_FORMAT))
    ttk.Label(frame, text="формат: ДД.ММ.ГГГГ ЧЧ:ММ", foreground="gray").grid(
        row=3, column=1, sticky="e"
    )

    ttk.Label(frame, text="Комментарий:").grid(row=4, column=0, sticky="nw", pady=3)
    comment_text = tk.Text(frame, width=44, height=5, wrap="word")
    comment_text.grid(row=4, column=1, pady=3)

    error = tk.Label(frame, text="", fg="#c62828")
    error.grid(row=5, column=0, columnspan=2, sticky="w")

    def save() -> None:
        try:
            submit(
                project_box.get(),
                kind_by_label[kind_box.get()],
                comment_text.get("1.0", "end"),
                start_entry.get(),
                end_entry.get(),
            )
        except DomainError as exc:
            error.config(text=str(exc))
            return
        saved["value"] = True
        win.destroy()

    buttons = ttk.Frame(frame)
    buttons.grid(row=6, column=0, columnspan=2, pady=(8, 0), sticky="e")
    ttk.Button(buttons, text="Сохранить", command=save).pack(side="left", padx=4)
    ttk.Button(buttons, text="Отмена", command=win.destroy).pack(side="left", padx=4)

    win.bind("<Escape>", lambda _e: win.destroy())
    win.lift()
    win.focus_force()
    comment_text.focus_set()
    root.wait_window(win)
    return saved["value"]

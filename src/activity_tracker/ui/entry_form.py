"""Форма ручного добавления записи (Tkinter)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from activity_tracker.domain.errors import DomainError
from activity_tracker.presentation.journal_view import NewEntryDefaults, NewEntrySubmit


def open_entry_form(
    root: tk.Misc, projects: list[str], defaults: NewEntryDefaults, submit: NewEntrySubmit
) -> bool:
    """Модальная форма. True, если запись сохранена."""
    saved = {"value": False}

    win = tk.Toplevel(root)
    win.title("Новая запись")
    win.resizable(False, False)

    frame = ttk.Frame(win, padding=15)
    frame.grid()

    ttk.Label(frame, text="Проект:").grid(row=0, column=0, sticky="w", pady=3)
    project_box = ttk.Combobox(frame, values=projects, width=42)
    project_box.grid(row=0, column=1, sticky="w", pady=3)
    project_box.set(defaults.project)

    ttk.Label(frame, text="Что это было:").grid(row=1, column=0, sticky="w", pady=3)
    kind_box = ttk.Combobox(frame, values=list(defaults.kind_labels), state="readonly", width=20)
    kind_box.grid(row=1, column=1, sticky="w", pady=3)
    kind_box.set(defaults.kind_label)

    ttk.Label(frame, text="Начало:").grid(row=2, column=0, sticky="w", pady=3)
    start_entry = ttk.Entry(frame, width=20)
    start_entry.grid(row=2, column=1, sticky="w", pady=3)
    start_entry.insert(0, defaults.start_text)

    ttk.Label(frame, text="Конец:").grid(row=3, column=0, sticky="w", pady=3)
    end_entry = ttk.Entry(frame, width=20)
    end_entry.grid(row=3, column=1, sticky="w", pady=3)
    end_entry.insert(0, defaults.end_text)
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
                kind_box.get(),
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

"""Окно вопроса (Tkinter). Тонкий слой: правила валидации живут в домене."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from activity_tracker.domain.errors import DomainError
from activity_tracker.domain.model import ActivityKind

# (подпись, вид активности, цвет)
KIND_BUTTONS = [
    ("Изучил", ActivityKind.LEARNED, "#c8e6c9"),
    ("Выполнил", ActivityKind.DONE, "#bbdefb"),
    ("Просто гуглил", ActivityKind.BROWSING, "#ffe0b2"),
]

# project_name, kind, comment -> сохраняет или бросает DomainError
SubmitFn = Callable[[str, ActivityKind, str], object]


def ask_user(root: tk.Tk, projects: list[str], submit: SubmitFn, idle_minutes: int) -> bool:
    """Показывает модальное окно. True, если ответ принят; False, если окно закрыли."""
    answered = {"value": False}

    win = tk.Toplevel(root)
    win.title("Что ты делал?")
    win.attributes("-topmost", True)
    win.resizable(False, False)

    pad = {"padx": 20}
    tk.Label(
        win,
        text=f"Ты {idle_minutes} мин. ничего не трогал.\nНад чем ты работал?",
        font=("Arial", 13),
    ).pack(pady=(15, 10), **pad)

    tk.Label(win, text="Проект (выбери или впиши новый):").pack(anchor="w", **pad)
    project_box = ttk.Combobox(win, values=projects, width=48)
    project_box.pack(pady=(0, 10), **pad)
    if projects:
        project_box.set(projects[0])

    tk.Label(win, text="Что делал:").pack(anchor="w", **pad)
    comment_text = tk.Text(win, width=48, height=5, wrap="word")
    comment_text.pack(pady=(0, 5), **pad)

    error = tk.Label(win, text="", fg="#c62828")
    error.pack(**pad)

    def choose(kind: ActivityKind) -> None:
        try:
            submit(project_box.get(), kind, comment_text.get("1.0", "end"))
        except DomainError as exc:
            error.config(text=str(exc))
            return
        answered["value"] = True
        win.destroy()

    buttons = tk.Frame(win)
    buttons.pack(pady=(5, 15))
    for label, kind, color in KIND_BUTTONS:
        tk.Button(
            buttons, text=label, width=13, bg=color, command=lambda k=kind: choose(k)
        ).pack(side="left", padx=6)

    win.update_idletasks()
    x = (win.winfo_screenwidth() - win.winfo_width()) // 2
    y = (win.winfo_screenheight() - win.winfo_height()) // 3
    win.geometry(f"+{x}+{y}")
    win.focus_force()
    comment_text.focus_set()

    root.wait_window(win)
    return answered["value"]

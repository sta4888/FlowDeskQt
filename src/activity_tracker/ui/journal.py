"""Главное окно: просмотр, фильтрация, ручное добавление и удаление записей."""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk
from typing import Callable

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.errors import DomainError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryFilter

from .entry_form import open_entry_form
from .formatting import KIND_LABELS, format_row, summarize
from .parsing import DISPLAY_DATE_FORMAT, parse_date, parse_datetime

ALL = "Все"
ERROR_COLOR = "#c62828"


class JournalWindow:
    def __init__(self, root: tk.Tk, service: TrackerService, on_quit: Callable[[], None]) -> None:
        self.root = root
        self.service = service
        self._on_quit = on_quit
        self._kind_by_label = {KIND_LABELS[k]: k for k in ActivityKind}
        self._comments: dict[str, str] = {}

        root.title("Журнал активности")
        root.geometry("1000x580")
        root.minsize(780, 420)

        self._build_filters()
        self._build_table()
        self._build_details()
        self._build_bottom_bar()

        self.refresh_projects()
        self.refresh()

    # ---------- построение окна ----------

    def _build_filters(self) -> None:
        bar = ttk.Frame(self.root, padding=(10, 10, 10, 4))
        bar.pack(fill="x")

        ttk.Label(bar, text="Проект:").grid(row=0, column=0, sticky="w")
        self.project_var = tk.StringVar(value=ALL)
        self.project_box = ttk.Combobox(bar, textvariable=self.project_var, state="readonly", width=24)
        self.project_box.grid(row=0, column=1, padx=(4, 14))
        self.project_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(bar, text="Тип:").grid(row=0, column=2, sticky="w")
        self.kind_var = tk.StringVar(value=ALL)
        kind_box = ttk.Combobox(
            bar, textvariable=self.kind_var, state="readonly", width=16,
            values=[ALL, *self._kind_by_label],
        )
        kind_box.grid(row=0, column=3, padx=(4, 14))
        kind_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(bar, text="Поиск:").grid(row=0, column=4, sticky="w")
        self.text_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.text_var, width=26).grid(row=0, column=5, padx=4)
        self.text_var.trace_add("write", lambda *_: self.refresh())

        ttk.Label(bar, text="С:").grid(row=1, column=0, sticky="e", pady=(6, 0))
        self.from_var = tk.StringVar()
        from_entry = ttk.Entry(bar, textvariable=self.from_var, width=12)
        from_entry.grid(row=1, column=1, sticky="w", padx=4, pady=(6, 0))

        ttk.Label(bar, text="По:").grid(row=1, column=2, sticky="e", pady=(6, 0))
        self.to_var = tk.StringVar()
        to_entry = ttk.Entry(bar, textvariable=self.to_var, width=12)
        to_entry.grid(row=1, column=3, sticky="w", padx=4, pady=(6, 0))

        for entry in (from_entry, to_entry):
            entry.bind("<Return>", lambda _e: self.refresh())
            entry.bind("<FocusOut>", lambda _e: self.refresh())

        presets = ttk.Frame(bar)
        presets.grid(row=1, column=5, sticky="w", pady=(6, 0))
        ttk.Button(presets, text="Сегодня", width=9, command=self._preset_today).pack(side="left", padx=2)
        ttk.Button(presets, text="7 дней", width=9, command=self._preset_week).pack(side="left", padx=2)
        ttk.Button(presets, text="Сбросить", width=9, command=self._reset_filters).pack(side="left", padx=2)

        ttk.Label(bar, text="даты: ДД.ММ.ГГГГ", foreground="gray").grid(
            row=2, column=0, columnspan=4, sticky="w", padx=4
        )

    def _build_table(self) -> None:
        frame = ttk.Frame(self.root, padding=(10, 4))
        frame.pack(fill="both", expand=True)

        columns = ("date", "time", "duration", "project", "kind", "comment")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        headings = [
            ("date", "Дата", 90, "w", False),
            ("time", "Время", 105, "w", False),
            ("duration", "Длит.", 80, "w", False),
            ("project", "Проект", 160, "w", False),
            ("kind", "Тип", 110, "w", False),
            ("comment", "Комментарий", 400, "w", True),
        ]
        for name, title, width, anchor, stretch in headings:
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, anchor=anchor, stretch=stretch)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._show_details())
        self.tree.bind("<Delete>", lambda _e: self.delete_selected())

    def _build_details(self) -> None:
        box = ttk.LabelFrame(self.root, text="Полный комментарий", padding=6)
        box.pack(fill="x", padx=10, pady=(4, 0))
        self.details = tk.Text(box, height=4, wrap="word", state="disabled", bg="#f6f6f6")
        self.details.pack(fill="x")

    def _build_bottom_bar(self) -> None:
        bar = ttk.Frame(self.root, padding=10)
        bar.pack(fill="x")
        ttk.Button(bar, text="Добавить запись…", command=self.add_entry).pack(side="left")
        ttk.Button(bar, text="Удалить выбранную", command=self.delete_selected).pack(side="left", padx=8)
        self.status = tk.Label(bar, text="", anchor="w")
        self.status.pack(side="left", padx=16)
        ttk.Button(bar, text="Выйти из трекера", command=self._on_quit).pack(side="right")

    # ---------- данные ----------

    def refresh_projects(self) -> None:
        values = [ALL, *self.service.list_projects()]
        self.project_box.configure(values=values)
        if self.project_var.get() not in values:
            self.project_var.set(ALL)

    def _criteria(self) -> EntryFilter:
        project = self.project_var.get()
        kind = self.kind_var.get()
        return EntryFilter(
            project_name=None if project == ALL else project,
            kind=None if kind == ALL else self._kind_by_label[kind],
            date_from=parse_date(self.from_var.get()),
            date_to=parse_date(self.to_var.get()),
            text=self.text_var.get(),
        )

    def refresh(self) -> None:
        try:
            criteria = self._criteria()
        except DomainError as exc:  # неверная дата: оставляем прежний список
            self.status.config(text=str(exc), fg=ERROR_COLOR)
            return

        views = self.service.search_entries(criteria)
        self.tree.delete(*self.tree.get_children())
        self._comments = {}
        for view in views:
            iid = str(view.id)
            self._comments[iid] = view.comment
            self.tree.insert("", "end", iid=iid, values=format_row(view))
        self.status.config(text=summarize(views), fg="black")
        self._show_details()

    def _show_details(self) -> None:
        selection = self.tree.selection()
        text = self._comments.get(selection[0], "") if selection else ""
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")

    # ---------- фильтры-пресеты ----------

    def _set_dates(self, start: date | None, end: date | None) -> None:
        self.from_var.set(start.strftime(DISPLAY_DATE_FORMAT) if start else "")
        self.to_var.set(end.strftime(DISPLAY_DATE_FORMAT) if end else "")
        self.refresh()

    def _preset_today(self) -> None:
        today = date.today()
        self._set_dates(today, today)

    def _preset_week(self) -> None:
        today = date.today()
        self._set_dates(today - timedelta(days=6), today)

    def _reset_filters(self) -> None:
        self.project_var.set(ALL)
        self.kind_var.set(ALL)
        self.text_var.set("")
        self._set_dates(None, None)

    # ---------- действия ----------

    def add_entry(self) -> None:
        def submit(project, kind, comment, started_text, ended_text):
            self.service.add_manual_entry(
                project, kind, comment, parse_datetime(started_text), parse_datetime(ended_text)
            )

        if open_entry_form(self.root, self.service.list_projects(), submit):
            self.refresh_projects()
            self.refresh()

    def delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        if messagebox.askyesno("Удаление", "Удалить выбранную запись?", parent=self.root):
            self.service.delete_entry(int(selection[0]))
            self.refresh_projects()
            self.refresh()

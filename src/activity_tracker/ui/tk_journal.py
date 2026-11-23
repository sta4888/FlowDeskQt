"""Tk-реализация окна журнала. Только виджеты: вся логика в JournalPresenter."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional, Sequence

from activity_tracker.presentation.journal_presenter import JournalPresenter
from activity_tracker.presentation.journal_view import (
    ALL, KIND_FILTER_CHOICES, FilterInput, JournalRow, JournalView, NewEntryDefaults, NewEntrySubmit,
)

from .entry_form import open_entry_form

ERROR_COLOR = "#c62828"


class TkJournalView(JournalView):
    def __init__(self, root: tk.Tk, on_quit: Callable[[], None]) -> None:
        self.root = root
        self._on_quit = on_quit
        self._presenter: Optional[JournalPresenter] = None
        self._muted = False  # true, пока поля меняет презентер, а не пользователь

        root.title("Журнал активности")
        root.geometry("1000x580")
        root.minsize(780, 420)

        self._build_filters()
        self._build_table()
        self._build_details()
        self._build_bottom_bar()

    def attach(self, presenter: JournalPresenter) -> None:
        self._presenter = presenter

    # ---------- JournalView ----------

    def show_rows(self, rows: Sequence[JournalRow]) -> None:
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", iid=str(row.id), values=row.cells)

    def show_status(self, text: str, is_error: bool) -> None:
        self.status.config(text=text, fg=ERROR_COLOR if is_error else "black")

    def show_details(self, comment: str) -> None:
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", comment)
        self.details.configure(state="disabled")

    def set_project_choices(self, choices: list[str]) -> None:
        self.project_box.configure(values=choices)

    def set_filter_inputs(self, inputs: FilterInput) -> None:
        self._muted = True
        try:
            self.project_var.set(inputs.project)
            self.kind_var.set(inputs.kind)
            self.from_var.set(inputs.date_from)
            self.to_var.set(inputs.date_to)
            self.text_var.set(inputs.text)
        finally:
            self._muted = False

    def confirm_delete(self) -> bool:
        return messagebox.askyesno("Удаление", "Удалить выбранную запись?", parent=self.root)

    def ask_new_entry(
        self, projects: list[str], defaults: NewEntryDefaults, submit: NewEntrySubmit
    ) -> bool:
        return open_entry_form(self.root, projects, defaults, submit)

    # ---------- события виджетов -> презентер ----------

    def _read_inputs(self) -> FilterInput:
        return FilterInput(
            project=self.project_var.get(),
            kind=self.kind_var.get(),
            date_from=self.from_var.get(),
            date_to=self.to_var.get(),
            text=self.text_var.get(),
        )

    def _on_inputs_changed(self, *_args) -> None:
        if self._muted or self._presenter is None:
            return
        self._presenter.on_inputs_changed(self._read_inputs())

    def _selected_id(self) -> Optional[int]:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _on_select(self, _event=None) -> None:
        if self._presenter is not None:
            self._presenter.on_selection_changed(self._selected_id())

    def _call(self, method_name: str) -> None:
        if self._presenter is not None:
            getattr(self._presenter, method_name)()

    # ---------- построение окна ----------

    def _build_filters(self) -> None:
        bar = ttk.Frame(self.root, padding=(10, 10, 10, 4))
        bar.pack(fill="x")

        ttk.Label(bar, text="Проект:").grid(row=0, column=0, sticky="w")
        self.project_var = tk.StringVar(value=ALL)
        self.project_box = ttk.Combobox(bar, textvariable=self.project_var, state="readonly", width=24)
        self.project_box.grid(row=0, column=1, padx=(4, 14))
        self.project_box.bind("<<ComboboxSelected>>", self._on_inputs_changed)

        ttk.Label(bar, text="Тип:").grid(row=0, column=2, sticky="w")
        self.kind_var = tk.StringVar(value=ALL)
        kind_box = ttk.Combobox(
            bar, textvariable=self.kind_var, state="readonly", width=16,
            values=list(KIND_FILTER_CHOICES),
        )
        kind_box.grid(row=0, column=3, padx=(4, 14))
        kind_box.bind("<<ComboboxSelected>>", self._on_inputs_changed)

        ttk.Label(bar, text="Поиск:").grid(row=0, column=4, sticky="w")
        self.text_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.text_var, width=26).grid(row=0, column=5, padx=4)
        self.text_var.trace_add("write", self._on_inputs_changed)

        ttk.Label(bar, text="С:").grid(row=1, column=0, sticky="e", pady=(6, 0))
        self.from_var = tk.StringVar()
        from_entry = ttk.Entry(bar, textvariable=self.from_var, width=12)
        from_entry.grid(row=1, column=1, sticky="w", padx=4, pady=(6, 0))

        ttk.Label(bar, text="По:").grid(row=1, column=2, sticky="e", pady=(6, 0))
        self.to_var = tk.StringVar()
        to_entry = ttk.Entry(bar, textvariable=self.to_var, width=12)
        to_entry.grid(row=1, column=3, sticky="w", padx=4, pady=(6, 0))

        for entry in (from_entry, to_entry):  # даты применяем по Enter/уходу из поля, не на каждую букву
            entry.bind("<Return>", self._on_inputs_changed)
            entry.bind("<FocusOut>", self._on_inputs_changed)

        presets = ttk.Frame(bar)
        presets.grid(row=1, column=5, sticky="w", pady=(6, 0))
        ttk.Button(presets, text="Сегодня", width=9,
                   command=lambda: self._call("preset_today")).pack(side="left", padx=2)
        ttk.Button(presets, text="7 дней", width=9,
                   command=lambda: self._call("preset_week")).pack(side="left", padx=2)
        ttk.Button(presets, text="Сбросить", width=9,
                   command=lambda: self._call("reset_filters")).pack(side="left", padx=2)

        ttk.Label(bar, text="даты: ДД.ММ.ГГГГ", foreground="gray").grid(
            row=2, column=0, columnspan=4, sticky="w", padx=4
        )

    def _build_table(self) -> None:
        frame = ttk.Frame(self.root, padding=(10, 4))
        frame.pack(fill="both", expand=True)

        columns = ("date", "time", "duration", "project", "kind", "comment")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        headings = [
            ("date", "Дата", 90, False),
            ("time", "Время", 105, False),
            ("duration", "Длит.", 80, False),
            ("project", "Проект", 160, False),
            ("kind", "Тип", 110, False),
            ("comment", "Комментарий", 400, True),
        ]
        for name, title, width, stretch in headings:
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, anchor="w", stretch=stretch)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Delete>", lambda _e: self._delete_selected())

    def _build_details(self) -> None:
        box = ttk.LabelFrame(self.root, text="Полный комментарий", padding=6)
        box.pack(fill="x", padx=10, pady=(4, 0))
        self.details = tk.Text(box, height=4, wrap="word", state="disabled", bg="#f6f6f6")
        self.details.pack(fill="x")

    def _build_bottom_bar(self) -> None:
        bar = ttk.Frame(self.root, padding=10)
        bar.pack(fill="x")
        ttk.Button(bar, text="Добавить запись…", command=lambda: self._call("add_entry")).pack(side="left")
        ttk.Button(bar, text="Удалить выбранную", command=self._delete_selected).pack(side="left", padx=8)
        self.status = tk.Label(bar, text="", anchor="w")
        self.status.pack(side="left", padx=16)
        ttk.Button(bar, text="Выйти из трекера", command=self._on_quit).pack(side="right")

    def _delete_selected(self) -> None:
        if self._presenter is not None:
            self._presenter.delete_entry(self._selected_id())

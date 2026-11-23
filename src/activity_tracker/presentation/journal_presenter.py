"""Логика окна журнала. Не знает ни про Tk, ни про Qt."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Callable, Optional

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.errors import DomainError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryFilter

from .formatting import (
    KIND_LABELS, NEW_ENTRY_KINDS, format_row, kind_from_label, summarize,
)
from .journal_view import ALL, FilterInput, JournalRow, JournalView, NewEntryDefaults
from .parsing import DISPLAY_DATE_FORMAT, DISPLAY_DATETIME_FORMAT, parse_date, parse_datetime

DEFAULT_ENTRY_LENGTH = timedelta(minutes=30)


class JournalPresenter:
    def __init__(
        self,
        service: TrackerService,
        view: JournalView,
        today: Callable[[], date] = date.today,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._service = service
        self._view = view
        self._today = today
        self._now = now
        self._inputs = FilterInput()
        self._comments: dict[int, str] = {}

    # ---------- события от представления ----------

    def start(self) -> None:
        self.refresh_projects()
        self.refresh()

    def on_inputs_changed(self, inputs: FilterInput) -> None:
        self._inputs = inputs
        self.refresh()

    def on_selection_changed(self, entry_id: Optional[int]) -> None:
        text = self._comments.get(entry_id, "") if entry_id is not None else ""
        self._view.show_details(text)

    def preset_today(self) -> None:
        today = self._today()
        self._apply(replace(self._inputs, date_from=self._fmt(today), date_to=self._fmt(today)))

    def preset_week(self) -> None:
        today = self._today()
        self._apply(
            replace(
                self._inputs,
                date_from=self._fmt(today - timedelta(days=6)),
                date_to=self._fmt(today),
            )
        )

    def reset_filters(self) -> None:
        self._apply(FilterInput())

    def add_entry(self) -> None:
        projects = self._service.list_projects()
        now = self._now().replace(second=0, microsecond=0)
        defaults = NewEntryDefaults(
            project=projects[0] if projects else "",
            kind_label=KIND_LABELS[ActivityKind.LEARNED],
            kind_labels=tuple(KIND_LABELS[kind] for kind in NEW_ENTRY_KINDS),
            start_text=(now - DEFAULT_ENTRY_LENGTH).strftime(DISPLAY_DATETIME_FORMAT),
            end_text=now.strftime(DISPLAY_DATETIME_FORMAT),
        )
        if self._view.ask_new_entry(projects, defaults, self.submit_new_entry):
            self.refresh_projects()
            self.refresh()

    def submit_new_entry(
        self, project: str, kind_label: str, comment: str, start_text: str, end_text: str
    ) -> None:
        """Бросает DomainError, если ввод неверный: форма покажет текст пользователю."""
        self._service.add_manual_entry(
            project,
            kind_from_label(kind_label),
            comment,
            parse_datetime(start_text),
            parse_datetime(end_text),
        )

    def delete_entry(self, entry_id: Optional[int]) -> None:
        if entry_id is None:
            return
        if self._view.confirm_delete():
            self._service.delete_entry(entry_id)
            self.refresh_projects()
            self.refresh()

    # ---------- обновление экрана ----------

    def refresh_projects(self) -> None:
        choices = [ALL, *self._service.list_projects()]
        self._view.set_project_choices(choices)
        if self._inputs.project not in choices:
            self._inputs = replace(self._inputs, project=ALL)
            self._view.set_filter_inputs(self._inputs)

    def refresh(self) -> None:
        try:
            criteria = self._criteria()
        except DomainError as exc:  # неверная дата: оставляем прежний список
            self._view.show_status(str(exc), True)
            return

        views = self._service.search_entries(criteria)
        self._comments = {view.id: view.comment for view in views}
        rows = [JournalRow(v.id, format_row(v), v.comment) for v in views]
        self._view.show_rows(rows)
        self._view.show_status(summarize(views), False)
        self._view.show_details("")

    # ---------- внутреннее ----------

    def _apply(self, inputs: FilterInput) -> None:
        self._inputs = inputs
        self._view.set_filter_inputs(inputs)
        self.refresh()

    def _criteria(self) -> EntryFilter:
        inputs = self._inputs
        return EntryFilter(
            project_name=None if inputs.project == ALL else inputs.project,
            kind=None if inputs.kind == ALL else kind_from_label(inputs.kind),
            date_from=parse_date(inputs.date_from),
            date_to=parse_date(inputs.date_to),
            text=inputs.text,
        )

    @staticmethod
    def _fmt(day: date) -> str:
        return day.strftime(DISPLAY_DATE_FORMAT)

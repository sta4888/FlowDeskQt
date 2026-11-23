from __future__ import annotations

from typing import Callable, Optional, Sequence

from activity_tracker.application.ports import ActivityMonitor
from activity_tracker.domain.tracker import ActivityPeriod
from activity_tracker.presentation.journal_view import (
    FilterInput, JournalRow, JournalView, NewEntryDefaults,
)


class FakeView(JournalView):
    """Запоминает всё, что презентер приказал показать."""

    def __init__(self) -> None:
        self.rows: list[JournalRow] = []
        self.show_rows_calls = 0
        self.status = ("", False)
        self.details = ""
        self.project_choices: list[str] = []
        self.inputs: Optional[FilterInput] = None
        self.confirm_answer = True
        self.confirm_calls = 0
        self.new_entry_request: Optional[tuple] = None
        self.on_new_entry: Optional[Callable] = None  # сценарий поведения «пользователя» в форме

    def show_rows(self, rows: Sequence[JournalRow]) -> None:
        self.rows = list(rows)
        self.show_rows_calls += 1

    def show_status(self, text: str, is_error: bool) -> None:
        self.status = (text, is_error)

    def show_details(self, comment: str) -> None:
        self.details = comment

    def set_project_choices(self, choices: list[str]) -> None:
        self.project_choices = list(choices)

    def set_filter_inputs(self, inputs: FilterInput) -> None:
        self.inputs = inputs

    def confirm_delete(self) -> bool:
        self.confirm_calls += 1
        return self.confirm_answer

    def ask_new_entry(self, projects: list[str], defaults: NewEntryDefaults, submit) -> bool:
        self.new_entry_request = (projects, defaults)
        return self.on_new_entry(submit) if self.on_new_entry else False


class FakeMonitor(ActivityMonitor):
    def __init__(self, *periods: Optional[ActivityPeriod]) -> None:
        self._periods = list(periods)
        self.reset_calls = 0

    def start(self) -> None: ...
    def stop(self) -> None: ...

    def poll(self) -> Optional[ActivityPeriod]:
        return self._periods.pop(0) if self._periods else None

    def reset(self) -> None:
        self.reset_calls += 1

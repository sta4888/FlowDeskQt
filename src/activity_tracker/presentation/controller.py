"""Оркестрация «опросил монитор, показал вопрос, сохранил ответ». Без привязки к UI."""

from __future__ import annotations

from typing import Callable

from activity_tracker.application.ports import ActivityMonitor
from activity_tracker.application.services import TrackerService

from .formatting import kind_from_label

# project_name, kind_label, comment -> сохраняет или бросает DomainError
SubmitAnswer = Callable[[str, str, str], object]
# projects, submit, idle_minutes -> True, если ответ принят; False, если окно закрыли
AskQuestion = Callable[[list[str], SubmitAnswer, int], bool]


class TrackerController:
    def __init__(
        self,
        service: TrackerService,
        monitor: ActivityMonitor,
        ask_question: AskQuestion,
        idle_minutes: int,
        on_recorded: Callable[[], None] = lambda: None,
    ) -> None:
        self._service = service
        self._monitor = monitor
        self._ask = ask_question
        self._idle_minutes = idle_minutes
        self._on_recorded = on_recorded

    def tick(self) -> None:
        """Вызывать периодически (раз в секунду) из главного потока UI."""
        period = self._monitor.poll()
        if period is None:
            return

        def submit(project: str, kind_label: str, comment: str) -> object:
            return self._service.record_entry(period, kind_from_label(kind_label), project, comment)

        answered = self._ask(self._service.list_projects(), submit, self._idle_minutes)
        if not answered:
            self._service.record_skipped(period)
        self._monitor.reset()  # ввод во время ответа не считается новой активностью
        self._on_recorded()

"""Представление данных для таблицы. Без tkinter, поэтому легко тестируется."""

from __future__ import annotations

from datetime import timedelta

from activity_tracker.domain.model import ActivityKind
from activity_tracker.domain.queries import EntryView

KIND_LABELS = {
    ActivityKind.LEARNED: "Изучил",
    ActivityKind.DONE: "Выполнил",
    ActivityKind.BROWSING: "Просто гуглил",
    ActivityKind.SKIPPED: "Пропущено",
}


def format_duration(delta: timedelta) -> str:
    minutes = round(delta.total_seconds() / 60)
    if minutes < 1:
        return "< 1 мин"
    hours, rest = divmod(minutes, 60)
    return f"{hours} ч {rest:02d} мин" if hours else f"{rest} мин"


def format_row(view: EntryView) -> tuple[str, ...]:
    return (
        view.started_at.strftime("%d.%m.%Y"),
        f"{view.started_at:%H:%M}–{view.ended_at:%H:%M}",
        format_duration(view.duration),
        view.project_name or "—",
        KIND_LABELS[view.kind],
        " ".join(view.comment.split()),
    )


def summarize(views: list[EntryView]) -> str:
    text = f"Записей: {len(views)}"
    worked = sum(
        (v.duration for v in views if v.kind is not ActivityKind.SKIPPED), timedelta()
    )
    if worked > timedelta():
        text += f" · Время: {format_duration(worked)}"
    return text

"""Разбор введённых пользователем дат. Без tkinter, поэтому легко тестируется."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from activity_tracker.domain.errors import ValidationError

DISPLAY_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
DISPLAY_DATE_FORMAT = "%d.%m.%Y"

_DATETIME_FORMATS = (DISPLAY_DATETIME_FORMAT, "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")
_DATE_FORMATS = (DISPLAY_DATE_FORMAT, "%Y-%m-%d")


def parse_datetime(text: str) -> datetime:
    text = (text or "").strip()
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValidationError("Время нужно вводить так: ДД.ММ.ГГГГ ЧЧ:ММ (например 23.11.2026 14:30)")


def parse_date(text: str) -> Optional[date]:
    """Пустая строка означает «без ограничения»."""
    text = (text or "").strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValidationError("Дату нужно вводить так: ДД.ММ.ГГГГ (например 23.11.2026)")

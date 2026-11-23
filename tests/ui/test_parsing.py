from datetime import date, datetime

import pytest

from activity_tracker.domain.errors import ValidationError
from activity_tracker.ui.parsing import parse_date, parse_datetime


@pytest.mark.parametrize("text", ["23.11.2026 14:30", "2026-11-23 14:30", "  23.11.2026 14:30  "])
def test_parse_datetime_accepts_common_formats(text):
    assert parse_datetime(text) == datetime(2026, 11, 23, 14, 30)


@pytest.mark.parametrize("text", ["", "вчера", "23.11.2026", "32.13.2026 10:00"])
def test_parse_datetime_rejects_garbage_with_readable_error(text):
    with pytest.raises(ValidationError, match="ДД.ММ.ГГГГ"):
        parse_datetime(text)


@pytest.mark.parametrize("text", ["23.11.2026", "2026-11-23"])
def test_parse_date_accepts_common_formats(text):
    assert parse_date(text) == date(2026, 11, 23)


@pytest.mark.parametrize("text", ["", "   "])
def test_parse_date_returns_none_for_empty_input(text):
    assert parse_date(text) is None


def test_parse_date_rejects_garbage():
    with pytest.raises(ValidationError, match="ДД.ММ.ГГГГ"):
        parse_date("завтра")

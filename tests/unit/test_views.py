"""Tests for the display helpers."""

from datetime import datetime, timedelta, timezone
from epicevents.views.console import format_datetime


def test_a_naive_date_is_written_as_it_is():
    """Keeps naive dates unchanged."""
    assert format_datetime(datetime(2026, 6, 4, 13, 0)) == "2026-06-04 13:00"


def test_an_aware_date_is_converted_to_the_local_time():
    """Converts aware dates to local time."""
    stored = datetime(2026, 6, 4, 13, 0, tzinfo=timezone.utc)
    assert format_datetime(stored) == stored.astimezone().strftime("%Y-%m-%d %H:%M")


def test_a_date_in_another_timezone_is_converted_too():
    """Converts dates from other timezones."""
    utc = datetime(2026, 6, 4, 13, 0, tzinfo=timezone.utc)
    same_moment = datetime(2026, 6, 4, 15, 0, tzinfo=timezone(timedelta(hours=2)))
    assert format_datetime(utc) == format_datetime(same_moment)

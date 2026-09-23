"""Tests for the display helpers."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from epicevents.views.console import (
    format_datetime,
    format_money,
    format_yes_no,
)


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


def test_an_amount_is_grouped_by_thousands():
    """Formats amounts with two decimals."""
    assert format_money(Decimal("12000")) == "12,000.00"
    assert format_money(Decimal("875.5")) == "875.50"


def test_a_small_amount_keeps_its_two_decimals():
    """Keeps two decimal places."""
    assert format_money(Decimal("0")) == "0.00"


def test_a_yes_and_a_no_are_told_apart():
    """Formats yes and no differently."""
    assert "yes" in format_yes_no(True)
    assert "no" in format_yes_no(False)
    assert format_yes_no(True) != format_yes_no(False)

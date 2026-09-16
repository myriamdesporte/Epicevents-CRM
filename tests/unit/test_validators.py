"""Tests for the validation of entered values."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from epicevents.validators import (
    ValidationError,
    validate_amount,
    validate_amount_due,
    validate_attendees,
    validate_date_range,
    validate_datetime,
    validate_email,
    validate_password,
    validate_phone,
    validate_required_text,
    validate_role_name,
)

# --------------------------------------------------------------------------
# Text
# --------------------------------------------------------------------------


def test_required_text_is_stripped():
    """Accepts required text and removes surrounding spaces."""
    cleaned = validate_required_text("  Kevin Casey  ", field="Name", max_length=100)

    assert cleaned == "Kevin Casey"


def test_empty_text_is_refused():
    """Refuses text containing only spaces."""
    with pytest.raises(ValidationError, match="required"):
        validate_required_text("   ", field="Name", max_length=100)


def test_text_longer_than_the_column_is_refused():
    """Refuses text longer than the allowed column length."""
    with pytest.raises(ValidationError, match="too long"):
        validate_required_text("x" * 101, field="Name", max_length=100)


# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------


def test_email_is_stripped_and_lowercased():
    """Accepts an email and normalizes spaces and letter case."""
    assert validate_email("  Bill@EpicEvents.FR ") == "bill@epicevents.fr"


@pytest.mark.parametrize(
    "wrong", ["", "bill", "bill@", "@epicevents.fr", "bill@epicevents", "a b@c.fr"]
)
def test_malformed_emails_are_refused(wrong):
    """Refuses emails that do not have a valid format."""
    with pytest.raises(ValidationError):
        validate_email(wrong)


# --------------------------------------------------------------------------
# Phone
# --------------------------------------------------------------------------


def test_phone_accepts_the_shapes_of_the_specification():
    """Accepts phone numbers matching the required formats."""
    assert validate_phone("+678 123 456 78") == "+678 123 456 78"
    assert validate_phone("+ 666 12345") == "+ 666 12345"


def test_phone_with_letters_is_refused():
    """Refuses phone numbers containing letters."""
    with pytest.raises(ValidationError, match="only contain"):
        validate_phone("call me")


def test_phone_with_too_few_digits_is_refused():
    """Refuses phone numbers containing too few digits."""
    with pytest.raises(ValidationError, match="digits"):
        validate_phone("+33")


# --------------------------------------------------------------------------
# Amounts
# --------------------------------------------------------------------------


def test_amount_is_returned_as_a_decimal():
    """Converts a valid amount to an exact Decimal value."""
    amount = validate_amount("1000.50", field="Total amount")

    assert amount == Decimal("1000.50")
    assert isinstance(amount, Decimal)


def test_amount_accepts_a_comma_as_decimal_separator():
    """Accepts a comma as the decimal separator."""
    assert validate_amount("1000,50", field="Total amount") == Decimal("1000.50")


def test_negative_amount_is_refused():
    """Refuses negative amounts."""
    with pytest.raises(ValidationError, match="negative"):
        validate_amount("-10", field="Total amount")


def test_unreadable_amount_is_refused():
    """Refuses amounts that cannot be converted to a number."""
    with pytest.raises(ValidationError, match="not a valid amount"):
        validate_amount("beaucoup", field="Total amount")


def test_amount_due_may_equal_the_total():
    """Accepts an unpaid contract where the amount due equals the total."""
    assert validate_amount_due("1000.00", "1000.00") == Decimal("1000.00")


def test_amount_due_above_the_total_is_refused():
    """Refuses an amount due that exceeds the contract total."""
    with pytest.raises(ValidationError, match="cannot exceed"):
        validate_amount_due("1500.00", "1000.00")


# --------------------------------------------------------------------------
# Attendees
# --------------------------------------------------------------------------


def test_attendees_is_returned_as_an_integer():
    """Converts a valid attendee count to an integer."""
    assert validate_attendees(" 75 ") == 75


@pytest.mark.parametrize("wrong", ["0", "-5"])
def test_attendees_must_be_positive(wrong):
    """Refuses attendee counts below one."""
    with pytest.raises(ValidationError, match="at least one attendee"):
        validate_attendees(wrong)


def test_attendees_that_is_not_a_number_is_refused():
    """Refuses attendee counts that are not whole numbers."""
    with pytest.raises(ValidationError, match="whole number"):
        validate_attendees("beaucoup")


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------


def test_datetime_is_returned_aware_and_in_utc():
    """Converts a local date and time to a timezone-aware UTC datetime."""
    parsed = validate_datetime("2026-06-04 13:00", field="Start date")

    assert parsed.tzinfo == timezone.utc


def test_datetime_in_the_wrong_format_is_refused():
    """Refuses dates that do not use the expected format."""
    with pytest.raises(ValidationError, match="must look like"):
        validate_datetime("04/06/2026", field="Start date")


def test_an_already_aware_datetime_goes_through():
    """Accepts an already timezone-aware datetime unchanged."""
    given = datetime(2026, 6, 4, 13, 0, tzinfo=timezone.utc)

    assert validate_datetime(given, field="Start date") == given


def test_date_range_is_accepted_in_order():
    """Accepts a date range when the end is after the start."""
    start, end = validate_date_range("2026-06-04 13:00", "2026-06-05 02:00")

    assert start < end


def test_end_before_start_is_refused():
    """Refuses a date range when the end is before the start."""
    with pytest.raises(ValidationError, match="after its beginning"):
        validate_date_range("2026-06-05 02:00", "2026-06-04 13:00")


def test_end_equal_to_start_is_refused():
    """Refuses a date range with identical start and end times."""
    with pytest.raises(ValidationError, match="after its beginning"):
        validate_date_range("2026-06-04 13:00", "2026-06-04 13:00")


# --------------------------------------------------------------------------
# Password and role
# --------------------------------------------------------------------------


def test_password_is_not_stripped():
    """Preserves spaces because they can be part of a password."""
    password = "  espaces autour  "

    assert validate_password(password) == password


def test_too_short_password_is_refused():
    """Refuses passwords shorter than the minimum length."""
    with pytest.raises(ValidationError, match="at least"):
        validate_password("court")


def test_role_name_is_cleaned():
    """Accepts a role and normalizes its spaces and letter case."""
    assert validate_role_name("  SALES ", {"sales", "support"}) == "sales"


def test_unknown_role_name_is_refused():
    """Refuses role names that are not in the allowed roles."""
    with pytest.raises(ValidationError, match="not a known role"):
        validate_role_name("intern", {"sales", "support"})

"""Validation of the values entered by a collaborator."""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PHONE_PATTERN = re.compile(r"^[0-9+().\-\s]+$")
MIN_PHONE_DIGITS = 6

MIN_PASSWORD_LENGTH = 12

DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATETIME_EXAMPLE = "2026-06-04 13:00"


class ValidationError(Exception):
    """Raised when a value entered by a collaborator cannot be accepted."""


def validate_required_text(value: str, *, field: str, max_length: int) -> str:
    """Return the value stripped, refusing an empty or too long one."""
    cleaned = (value or "").strip()

    if not cleaned:
        raise ValidationError(f"{field} is required.")

    if len(cleaned) > max_length:
        raise ValidationError(
            f"{field} is too long: {len(cleaned)} characters, "
            f"{max_length} allowed at most."
        )

    return cleaned


def validate_email(value: str) -> str:
    """Return the email stripped and lowercased, refusing a malformed one."""
    cleaned = (value or "").strip().lower()

    if not cleaned:
        raise ValidationError("Email is required.")

    if not EMAIL_PATTERN.match(cleaned):
        raise ValidationError(f"'{cleaned}' is not a valid email address.")

    return cleaned


def validate_phone(value: str) -> str:
    """Return the phone number stripped, refusing an implausible one."""
    cleaned = (value or "").strip()

    if not cleaned:
        raise ValidationError("Phone number is required.")

    if not PHONE_PATTERN.match(cleaned):
        raise ValidationError(
            "A phone number may only contain digits, spaces and + ( ) . -"
        )

    digits = sum(character.isdigit() for character in cleaned)
    if digits < MIN_PHONE_DIGITS:
        raise ValidationError(
            f"A phone number needs at least {MIN_PHONE_DIGITS} digits."
        )

    return cleaned


def validate_amount(value, *, field: str) -> Decimal:
    """Return the amount as a Decimal, refusing a negative or unreadable one."""
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValidationError(f"{field} is not a valid amount: '{value}'.") from None

    if amount < 0:
        raise ValidationError(f"{field} cannot be negative.")

    return amount


def validate_amount_due(amount_due, total_amount) -> Decimal:
    """Return the amount still due, refusing more than the total."""
    due = validate_amount(amount_due, field="Amount due")
    total = validate_amount(total_amount, field="Total amount")

    if due > total:
        raise ValidationError(
            f"Amount due ({due}) cannot exceed the total amount ({total})."
        )

    return due


def validate_attendees(value) -> int:
    """Return the number of attendees, refusing zero or a negative number."""
    try:
        attendees = int(str(value).strip())
    except (ValueError, AttributeError):
        raise ValidationError(
            f"The number of attendees must be a whole number: '{value}'."
        ) from None

    if attendees <= 0:
        raise ValidationError("An event needs at least one attendee.")

    return attendees


def validate_datetime(value, *, field: str) -> datetime:
    """Return the date and time as a timezone-aware UTC datetime."""
    if not isinstance(value, datetime):
        try:
            value = datetime.strptime(str(value).strip(), DATETIME_FORMAT)
        except ValueError:
            raise ValidationError(
                f"{field} must look like: '{DATETIME_EXAMPLE}'."
            ) from None

    return value.astimezone(timezone.utc)


def validate_date_range(start, end) -> tuple[datetime, datetime]:
    """Return the two dates, refusing an end before or equal to the start."""
    start_date = validate_datetime(start, field="Start date")
    end_date = validate_datetime(end, field="End date")

    if end_date <= start_date:
        raise ValidationError("The end of an event must come after its beginning.")

    return start_date, end_date


def validate_password(value: str) -> str:
    """Return the password unchanged, refusing a too short one."""
    if not value or len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"A password needs at least {MIN_PASSWORD_LENGTH} characters."
        )

    return value


def validate_role_name(value: str, allowed: set[str]) -> str:
    """Return the role name, refusing one that does not exist."""
    cleaned = (value or "").strip().lower()

    if cleaned not in allowed:
        raise ValidationError(
            f"'{value}' is not a known role. Known roles: "
            f"{', '.join(sorted(allowed))}."
        )

    return cleaned

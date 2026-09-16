"""Turning expected failures into readable messages."""

import functools

from sqlalchemy.exc import OperationalError

from epicevents.services.auth import AuthenticationError, AuthorizationError
from epicevents.validators import ValidationError
from epicevents.views.console import print_error

DATABASE_UNREACHABLE = (
    "Cannot reach the database. Is the container running?\n"
    "  Start it with: docker compose up -d"
)


def handle_errors(command):
    """Report an expected failure as a message, and exit with a non-zero code."""

    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        try:
            return command(*args, **kwargs)
        except (AuthenticationError, AuthorizationError, ValidationError) as error:
            print_error(str(error))
            raise SystemExit(1)
        except OperationalError:
            print_error(DATABASE_UNREACHABLE)
            raise SystemExit(1)

    return wrapper

"""Turning expected failures into readable messages."""

import functools

from sqlalchemy.exc import OperationalError, StatementError

from epicevents.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ValidationError,
)
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
        except (
            AuthenticationError,
            AuthorizationError,
            ValidationError,
            ConfigurationError,
        ) as error:
            print_error(str(error))
            raise SystemExit(1)
        except OperationalError:
            print_error(DATABASE_UNREACHABLE)
            raise SystemExit(1)
        except StatementError as error:
            # SQLAlchemy wraps an error raised while encrypting a searched value
            if isinstance(error.orig, ConfigurationError):
                print_error(str(error.orig))
                raise SystemExit(1)
            raise

    return wrapper

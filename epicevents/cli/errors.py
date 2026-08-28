"""Turning expected failures into readable messages."""

import functools

from sqlalchemy.exc import OperationalError

from epicevents.auth import AuthenticationError, AuthorizationError
from epicevents.cli.console import print_error

DATABASE_UNREACHABLE = (
    "Cannot reach the database. Is the container running?\n"
    " Start it with: docker compose up -d"
)


def handle_errors(command):
    """Report an expected failure as a message, and exit with a non-zero code.

    Without this, a wrong password would print a Python traceback: unreadable
    for the collaborator, and it would expose internal details of the
    application. Unexpected exceptions are deliberately left to propagate --
    they are bugs, and Sentry will report them.
    """

    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        try:
            return command(*args, **kwargs)
        except (AuthenticationError, AuthorizationError) as error:
            print_error(str(error))
            raise SystemExit(1)
        except OperationalError:
            print_error(DATABASE_UNREACHABLE)
            raise SystemExit(1)

    return wrapper

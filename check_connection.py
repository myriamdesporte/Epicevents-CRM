"""Check that the application can reach the database."""

import sys

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from epicevents.controllers.errors import DATABASE_UNREACHABLE
from epicevents.database import engine


def check_connection():
    """Open a connection and report the server version and current user."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version(), current_user;"))
        version, user = result.one()
        print(f"Connected : {version}")
        print(f"User : {user}")


if __name__ == "__main__":
    try:
        check_connection()
    except OperationalError:
        sys.exit(DATABASE_UNREACHABLE)

"""Check that the application can reach the database."""

from sqlalchemy import text
from epicevents.database import engine


def check_connection():
    """Open a connection and report the server version and current user."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version(), current_user;"))
        version, user = result.one()
        print(f"Connected : {version}")
        print(f"User : {user}")


if __name__ == "__main__":
    check_connection()

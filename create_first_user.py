"""Create the very first collaborator, in the management department."""

import getpass
import sys

from sqlalchemy import select

from epicevents.database import Session
from epicevents.models import Role, RoleName, User

MIN_PASSWORD_LENGTH = 12


def prompt_required(label: str) -> str:
    """Ask for a value until a non-empty one is given."""
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("This field is required.")


def prompt_password() -> str:
    """Ask for the password twice, without echoing it to the terminal."""
    while True:
        password = getpass.getpass("Password: ")
        if len(password) < MIN_PASSWORD_LENGTH:
            print(f"At least {MIN_PASSWORD_LENGTH} characters required.")
        elif password != getpass.getpass("Confirm password: "):
            print("Passwords do not match.")
        else:
            return password


def main() -> None:
    """Create the first management collaborator, or refuse to run."""
    with Session() as session:
        if session.scalar(select(User.id).limit(1)) is not None:
            sys.exit(
                "A user already exists: create collaborators from the application instead."
            )

        role = session.scalar(select(Role).where(Role.name == RoleName.MANAGEMENT))
        if role is None:
            sys.exit("Roles are missing: run 'python init_db.py first.")

        user = User(
            employee_number=prompt_required("Employee number"),
            full_name=prompt_required("Full name"),
            email=prompt_required("Email"),
            role_id=role.id,
        )
        user.set_password(prompt_password())

        session.add(user)
        session.commit()
        print(f"Management collaborator created: {user.email}")


if __name__ == "__main__":
    main()

"""Create the very first collaborator, in the management department."""

import getpass
import sys

from sqlalchemy import select

from epicevents.database import Session
from epicevents.models import Role, RoleName, User
from epicevents.validators import (
    ValidationError,
    validate_password,
    validate_required_text,
    validate_email,
)


def prompt(label: str, validate) -> str:
    """Ask for a value until the validators accepts it."""

    while True:
        try:
            return validate(input(f"{label}: "))
        except ValidationError as error:
            print(error)


def prompt_password() -> str:
    """Ask for the password twice, without echoing it to the terminal."""
    while True:
        try:
            password = validate_password(getpass.getpass("Password: "))
        except ValidationError as error:
            print(error)
            continue

        if password != getpass.getpass("Confirm password: "):
            print("Passwords do not match")
            continue

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
            employee_number=prompt(
                "Employee number",
                lambda value: validate_required_text(
                    value, field="Employee number", max_length=20
                ),
            ),
            full_name=prompt(
                "Full name",
                lambda value: validate_required_text(
                    value, field="Full name", max_length=100
                ),
            ),
            email=prompt("Email", validate_email),
            role_id=role.id,
        )
        user.set_password(prompt_password())

        session.add(user)
        session.commit()
        print(f"Management collaborator created: {user.email}")


if __name__ == "__main__":
    main()

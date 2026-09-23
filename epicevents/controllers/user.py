"""Collaborator commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.controllers.options import given
from epicevents.repositories import UserRepository
from epicevents.services import auth
from epicevents.services import user as user_service
from epicevents.validators import ValidationError
from epicevents.views import user as user_view


@click.group()
def user() -> None:
    """Collaborators."""


@user.command("list")
@handle_errors
def list_users() -> None:
    """List the collaborators."""
    with database.Session() as session:
        auth.get_current_user(session)
        user_view.show_list(UserRepository(session).list_all())


@user.command("create")
@click.option("--employee-number", prompt="Employee number")
@click.option("--full-name", prompt="Full name")
@click.option("--email", prompt="Email")
@click.option("--role", prompt="Role (sales, support or management)")
@handle_errors
def create_user(employee_number: str, full_name: str, email: str, role: str) -> None:
    """Create a collaborator. Management only."""
    # Asked for, never an option: a password given on the command line would
    # stay in the shell history and be visible in the process list.
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    with database.Session() as session:
        created = user_service.create_user(
            session,
            auth.get_current_user(session),
            employee_number=employee_number,
            full_name=full_name,
            email=email,
            password=password,
            role_name=role,
        )
        user_view.show_saved(created)


@user.command("update")
@click.argument("user_id", type=int)
@click.option("--employee-number")
@click.option("--full-name")
@click.option("--email")
@click.option("--role", help="Move the collaborator to another department.")
@click.option("--change-password", is_flag=True, help="Ask for a new password.")
@handle_errors
def update_user(
    user_id: int,
    employee_number: str,
    full_name: str,
    email: str,
    role: str,
    change_password: bool,
) -> None:
    """Update a collaborator. Management only."""
    changes = given(
        employee_number=employee_number,
        full_name=full_name,
        email=email,
        role_name=role,
    )

    if change_password:
        changes["password"] = click.prompt(
            "New password", hide_input=True, confirmation_prompt=True
        )

    if not changes:
        raise click.UsageError("Nothing to update: give at least one option.")

    with database.Session() as session:
        found = UserRepository(session).get(user_id)
        if found is None:
            raise ValidationError(f"No collaborator has the id {user_id}.")

        user_service.update_user(
            session, auth.get_current_user(session), found, **changes
        )
        user_view.show_saved(found)


@user.command("delete")
@click.argument("user_id", type=int)
@handle_errors
def delete_user(user_id: int) -> None:
    """Delete a collaborator. Management only."""
    with database.Session() as session:
        found = UserRepository(session).get(user_id)
        if found is None:
            raise ValidationError(f"No collaborator has the id {user_id}.")

        # Deleting is irreversible: ask before doing it.
        click.confirm(f"Delete {found.full_name}?", abort=True)

        user_service.delete_user(session, auth.get_current_user(session), found)
        user_view.show_deleted(found)

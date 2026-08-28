"""Session commands: login, logout, whoami."""

import click

from epicevents import auth, database
from epicevents.cli.console import print_details, print_success
from epicevents.cli.errors import handle_errors


@click.command()
@click.option("--email", prompt="Email", help="Your Epic Events email address.")
@handle_errors
def login(email: str) -> None:
    """Open a session on this machine."""
    password = click.prompt("Password", hide_input=True)

    with database.Session() as session:
        user = auth.login(session, email, password)
        print_success(f"Logged in as {user.full_name} ({user.role.name}).")


@click.command()
@handle_errors
def logout() -> None:
    """Forget the session stored on this machine."""
    auth.clear_token()
    print_success("Logged out.")


@click.command()
@handle_errors
def whoami() -> None:
    """Show the collaborator the current session belongs to."""
    with database.Session() as session:
        user = auth.get_current_user(session)
        print_details(
            "Current session",
            {
                "Employee number": user.employee_number,
                "Name": user.full_name,
                "Email": user.email,
                "Role": user.role.name,
            },
        )

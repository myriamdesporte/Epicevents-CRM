"""Session commands: login, logout, whoami."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.services import auth
from epicevents.views import user as user_view


@click.command()
@click.option("--email", prompt="Email", help="Your Epic Events email address.")
@handle_errors
def login(email: str) -> None:
    """Open a session on this machine."""
    password = click.prompt("Password", hide_input=True)

    with database.Session() as session:
        current_user = auth.login(session, email, password)
        user_view.show_login(current_user)


@click.command()
@handle_errors
def logout() -> None:
    """Forget the session stored on this machine."""
    auth.clear_token()
    user_view.show_logout()


@click.command()
@handle_errors
def whoami() -> None:
    """Show the collaborator the current session belongs to."""
    with database.Session() as session:
        current_user = auth.get_current_user(session)
        user_view.show_current_user(current_user)

"""Refusing a command before it asks for anything."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.services import auth


def requires(permission):
    """Requires the given permission before running the command."""

    @handle_errors
    def check(context, parameter, value) -> None:
        with database.Session() as session:
            auth.authorize(auth.get_current_user(session), permission)

    # Run the permission check before the command prompts.
    return click.option(
        "--permission-check",
        is_eager=True,
        expose_value=False,
        hidden=True,
        is_flag=True,
        callback=check,
    )

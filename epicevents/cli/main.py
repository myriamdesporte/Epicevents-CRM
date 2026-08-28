"""Command group of the Epic Events CRM."""

import click

from epicevents.cli import auth


@click.group()
def cli() -> None:
    """Epic Events CRM."""


cli.add_command(auth.login)
cli.add_command(auth.logout)
cli.add_command(auth.whoami)

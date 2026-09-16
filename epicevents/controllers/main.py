"""Command group of the Epic Events CRM."""

import click

from epicevents.controllers import auth, client, contract, event


@click.group()
def cli() -> None:
    """Epic Events CRM."""


# Session
cli.add_command(auth.login)
cli.add_command(auth.logout)
cli.add_command(auth.whoami)

# Business data
cli.add_command(client.client)
cli.add_command(contract.contract)
cli.add_command(event.event)

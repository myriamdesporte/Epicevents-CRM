"""Client commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.repositories import ClientRepository
from epicevents.services import auth
from epicevents.views import client as client_view


@click.group()
def client() -> None:
    """Clients."""


@client.command("list")
@click.option("--mine", is_flag=True, help="Only the clients you are the contact of.")
@handle_errors
def list_clients(mine: bool) -> None:
    """List the clients."""
    with database.Session() as session:
        # Reading requires a valid session but no particular permission: the
        # specification grants read access to every collaborator.
        current_user = auth.get_current_user(session)

        repository = ClientRepository(session)

        if mine:
            clients = repository.list_for_sales_contact(current_user.id)
        else:
            clients = repository.list_all()

        client_view.show_clients(clients)

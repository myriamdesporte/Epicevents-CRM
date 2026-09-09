"""Client commands."""

import click

from epicevents import auth, database
from epicevents.cli.console import print_info, print_table
from epicevents.cli.errors import handle_errors
from epicevents.repositories import ClientRepository

COLUMNS = ("ID", "Name", "Company", "Email", "Phone", "Sales contact")


def as_row(client) -> tuple[str, ...]:
    """Turn a client into the cells of a table row."""
    return (
        str(client.id),
        client.full_name,
        client.company_name,
        client.email,
        client.phone,
        client.sales_contact.full_name,
    )


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
        user = auth.get_current_user(session)

        repository = ClientRepository(session)

        if mine:
            clients = repository.list_for_sales_contact(user.id)
        else:
            clients = repository.list_all()

        if not clients:
            print_info("No client to display.")
            return

        print_table("Clients", COLUMNS, [as_row(found) for found in clients])

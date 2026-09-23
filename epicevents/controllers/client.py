"""Client commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.controllers.guards import requires
from epicevents.controllers.options import given
from epicevents.permissions import Permission
from epicevents.repositories import ClientRepository
from epicevents.services import auth
from epicevents.services import client as client_service
from epicevents.validators import ValidationError
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

        client_view.show_list(clients)


@client.command("create")
@requires(Permission.CLIENT_CREATE)
@click.option("--full-name", prompt="Full name")
@click.option("--email", prompt="Email")
@click.option("--phone", prompt="Phone")
@click.option("--company-name", prompt="Company name")
@handle_errors
def create_client(full_name: str, email: str, phone: str, company_name: str) -> None:
    """Create a client. Sales only, assigned to you automatically."""
    with database.Session() as session:
        created = client_service.create_client(
            session,
            auth.get_current_user(session),
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
        )
        client_view.show_saved(created)


@client.command("update")
@requires(Permission.CLIENT_UPDATE)
@click.argument("client_id", type=int)
@click.option("--full-name")
@click.option("--email")
@click.option("--phone")
@click.option("--company-name")
@handle_errors
def update_client(
    client_id: int,
    full_name: str,
    email: str,
    phone: str,
    company_name: str,
) -> None:
    """Update one of your own clients."""
    changes = given(
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name,
    )

    if not changes:
        raise click.UsageError("Nothing to update: give at least one option.")

    with database.Session() as session:
        found = ClientRepository(session).get(client_id)
        if found is None:
            raise ValidationError(f"No client has the id {client_id}.")

        client_service.update_client(
            session, auth.get_current_user(session), found, **changes
        )
        client_view.show_saved(found)


@client.command("show")
@click.argument("client_id", type=int)
@handle_errors
def show_client(client_id: int) -> None:
    """Show every field of one client."""
    with database.Session() as session:
        auth.get_current_user(session)

        found = ClientRepository(session).get(client_id)
        if found is None:
            raise ValidationError(f"No client has the id {client_id}.")

        client_view.show_details(found)

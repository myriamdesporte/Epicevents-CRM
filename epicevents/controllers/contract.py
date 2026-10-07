"""Contract commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.controllers.guards import requires
from epicevents.controllers.options import ask, given
from epicevents.permissions import Permission
from epicevents.repositories import ContractRepository
from epicevents.services import auth
from epicevents.services import contract as contract_service
from epicevents.validators import ValidationError
from epicevents.views import client as client_view
from epicevents.views import contract as contract_view


@click.group()
def contract() -> None:
    """Contracts."""


@contract.command("list")
@click.option("--unsigned", is_flag=True, help="Only the contracts not signed yet.")
@click.option("--unpaid", is_flag=True, help="Only the contracts still owing money.")
@click.option("--mine", is_flag=True, help="Only the contracts of your own clients.")
@handle_errors
def list_contracts(unsigned: bool, unpaid: bool, mine: bool) -> None:
    """List the contracts."""

    with database.Session() as session:
        current_user = auth.get_current_user(session)
        repository = ContractRepository(session)

        contracts = repository.list_filtered(
            unsigned=unsigned,
            unpaid=unpaid,
            sales_contact_id=current_user.id if mine else None,
        )

        contract_view.show_list(contracts)


def _find(session, contract_id: int):
    """Return the contract, or explain that the id is unknown."""
    found = ContractRepository(session).get(contract_id)
    if found is None:
        raise ValidationError(f"No contract has the id {contract_id}.")
    return found


@contract.command("create")
@requires(Permission.CONTRACT_CREATE)
@click.option("--client-id", type=int)
@click.option("--total-amount")
@click.option("--amount-due")
@click.option("--signed", is_flag=True, help="The client has already signed.")
@handle_errors
def create_contract(
    client_id: int, total_amount: str, amount_due: str, signed: bool
) -> None:
    """Create a contract for a client. Management only."""
    with database.Session() as session:
        current_user = auth.get_current_user(session)

        client = contract_service.client_for_new_contract(
            session, current_user, ask(client_id, "Client id", type=int)
        )
        client_view.show_selected(client)

        created = contract_service.create_contract(
            session,
            current_user,
            client_id=client.id,
            total_amount=ask(total_amount, "Total amount"),
            amount_due=ask(amount_due, "Amount still due"),
            is_signed=signed,
        )
        contract_view.show_saved(created)


@contract.command("update")
@requires(Permission.CONTRACT_UPDATE)
@click.argument("contract_id", type=int)
@click.option("--total-amount")
@click.option("--amount-due")
@handle_errors
def update_contract(contract_id: int, total_amount: str, amount_due: str) -> None:
    """Update the amounts of a contract."""
    changes = given(total_amount=total_amount, amount_due=amount_due)

    if not changes:
        raise click.UsageError("Nothing to update: give at least one option.")

    with database.Session() as session:
        found = _find(session, contract_id)
        contract_view.show_selected(found)
        contract_service.update_contract(
            session, auth.get_current_user(session), found, **changes
        )
        contract_view.show_saved(found)


@contract.command("sign")
@requires(Permission.CONTRACT_UPDATE)
@click.argument("contract_id", type=int)
@handle_errors
def sign_contract(contract_id: int) -> None:
    """Mark a contract as signed."""
    with database.Session() as session:
        found = _find(session, contract_id)

        contract_view.show_selected(found)
        click.confirm("Sign this contract?", abort=True)

        contract_service.sign_contract(session, auth.get_current_user(session), found)
        contract_view.show_saved(found)


@contract.command("show")
@click.argument("contract_id", type=int)
@handle_errors
def show_contract(contract_id: int) -> None:
    """Show every field of one contract."""
    with database.Session() as session:
        auth.get_current_user(session)
        contract_view.show_details(_find(session, contract_id))

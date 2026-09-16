"""Contract commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.repositories import ContractRepository
from epicevents.services import auth
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

        contract_view.show_contracts(contracts)

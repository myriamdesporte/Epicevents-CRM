"""Contract commands."""

import click

from epicevents import auth, database
from epicevents.cli.console import print_info, print_table
from epicevents.cli.errors import handle_errors
from epicevents.repositories import ContractRepository

COLUMNS = ("ID", "Client", "Sales contact", "Total", "Due", "Signed")


def as_row(contract) -> tuple[str, ...]:
    """Turn a contract into the cells of a table row."""
    return (
        str(contract.id),
        contract.client.full_name,
        # Reached through the client: a contract has no sales contact of its own.
        contract.client.sales_contact.full_name,
        f"{contract.total_amount:.2f}",
        f"{contract.amount_due:.2f}",
        "yes" if contract.is_signed else "no",
    )


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
        user = auth.get_current_user(session)
        repository = ContractRepository(session)

        contracts = repository.list_filtered(
            unsigned=unsigned,
            unpaid=unpaid,
            sales_contact_id=user.id if mine else None,
        )

        if not contracts:
            print_info("No contract to display.")
            return

        print_table("Contracts", COLUMNS, [as_row(found) for found in contracts])

"""Display of the contracts."""

from epicevents.views.console import print_info, print_table

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


def show_contracts(contracts) -> None:
    """Display a list of contracts, or say there is none."""
    if not contracts:
        print_info("No contract to display.")
        return

    print_table("Contracts", COLUMNS, [as_row(contract) for contract in contracts])

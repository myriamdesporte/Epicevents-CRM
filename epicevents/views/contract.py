"""Display of the contracts."""

from epicevents.views.console import print_info, print_table, print_success

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


def show_saved(contract) -> None:
    """Confirm that a contract was created or updated."""
    signed = "signed" if contract.is_signed else "not signed"
    print_success(
        f"Contract {contract.id} saved for {contract.client.full_name}: "
        f"{contract.amount_due:.2f} still due, {signed}."
    )

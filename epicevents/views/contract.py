"""Display of the contracts."""

from epicevents.views.console import (
    format_attention,
    format_datetime,
    format_money,
    format_yes_no,
    print_details,
    print_info,
    print_success,
    print_table,
)

COLUMNS = ("ID", "Client", "Sales contact", "Total", "Due", "Signed")

AMOUNTS = ("Total", "Due")


def format_due(amount) -> str:
    """Write an amount still due, highlighted unless it is nil."""
    if amount == 0:
        return format_money(amount)

    return format_attention(format_money(amount))


def as_row(contract) -> tuple[str, ...]:
    """Turn a contract into the cells of a table row."""
    return (
        str(contract.id),
        contract.client.full_name,
        # Reached through the client: a contract has no sales contact of its own.
        contract.client.sales_contact.full_name,
        format_money(contract.total_amount),
        format_due(contract.amount_due),
        format_yes_no(contract.is_signed),
    )


def show_list(contracts) -> None:
    """Display a list of contracts, or say there is none."""
    if not contracts:
        print_info("No contract to display.")
        return

    print_table(
        "Contracts",
        COLUMNS,
        [as_row(contract) for contract in contracts],
        right=AMOUNTS,
    )


def show_details(contract) -> None:
    """Display every field of one contract."""
    print_details(
        f"Contract {contract.id}",
        {
            "Client": contract.client.full_name,
            "Company": contract.client.company_name,
            "Sales contact": contract.client.sales_contact.full_name,
            "Total amount": format_money(contract.total_amount),
            "Amount due": format_due(contract.amount_due),
            "Signed": format_yes_no(contract.is_signed),
            "Created": format_datetime(contract.created_at),
            "Last update": format_datetime(contract.updated_at),
        },
    )


def show_saved(contract) -> None:
    """Confirm that a contract was created or updated."""
    signed = "signed" if contract.is_signed else "not signed"
    print_success(
        f"Contract {contract.id} saved for {contract.client.full_name}: "
        f"{format_money(contract.amount_due)} still due, {signed}."
    )

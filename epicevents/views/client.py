"""Display of the clients."""

from epicevents.views.console import print_info, print_table, print_success

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


def show_clients(clients) -> None:
    """Display a list of clients or none."""
    if not clients:
        print_info("No client to display.")
        return

    print_table("Clients", COLUMNS, [as_row(client) for client in clients])


def show_saved(client) -> None:
    """Confirm that a client was created or updated."""
    print_success(f"Client saved: {client.full_name} ({client.company_name}).")

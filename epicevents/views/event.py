"""Display of the events."""

from epicevents.views.console import (
    format_attention,
    format_datetime,
    print_details,
    print_info,
    print_success,
    print_table,
)

COLUMNS = ("ID", "Name", "Client", "Start", "End", "Attendees", "Support")

NUMBERS = ("Attendees",)
NO_SUPPORT = "unassigned"


def format_support(user) -> str:
    """Write the support contact, or highlight that there is none yet."""
    if user is None:
        return format_attention(NO_SUPPORT)

    return user.full_name


def as_row(event) -> tuple[str, ...]:
    """Turn an event into the cells of a table row."""
    return (
        str(event.id),
        event.name,
        event.contract.client.full_name,
        format_datetime(event.start_date),
        format_datetime(event.end_date),
        str(event.attendees),
        format_support(event.support_contact),
    )


def show_list(events) -> None:
    """Display a list of events, or say there is none."""
    if not events:
        print_info("No event to display.")
        return

    print_table("Events", COLUMNS, [as_row(event) for event in events], right=NUMBERS)


def show_details(event) -> None:
    """Display every field of one event."""
    client = event.contract.client

    print_details(
        f"Event {event.id} -- {event.name}",
        {
            "Contract": str(event.contract.id),
            "Client": client.full_name,
            "Client contact": f"{client.email} / {client.phone}",
            "Start": format_datetime(event.start_date),
            "End": format_datetime(event.end_date),
            "Location": event.location,
            "Attendees": str(event.attendees),
            "Support contact": format_support(event.support_contact),
            "Notes": event.notes or "-",
        },
    )


def show_saved(event) -> None:
    """Confirm that an event was created or updated."""
    support = format_support(event.support_contact)
    print_success(f"Event {event.id} saved: {event.name}, support: {support}.")

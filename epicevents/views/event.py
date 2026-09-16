"""Display of the events."""

from epicevents.views.console import print_info, print_table, print_success

COLUMNS = ("ID", "Name", "Client", "Start", "End", "Attendees", "Support")

DATE_FORMAT = "%Y-%m-%d %H:%M"

NO_SUPPORT = "-"


def as_row(event) -> tuple[str, ...]:
    """Turn an event into the cells of a table row."""
    return (
        str(event.id),
        event.name,
        event.contract.client.full_name,
        event.start_date.strftime(DATE_FORMAT),
        event.end_date.strftime(DATE_FORMAT),
        str(event.attendees),
        # An event may legitimately have no support contact yet.
        event.support_contact.full_name if event.support_contact else NO_SUPPORT,
    )


def show_events(events) -> None:
    """Display a list of events, or say there is none."""
    if not events:
        print_info("No event to display.")
        return

    print_table("Events", COLUMNS, [as_row(event) for event in events])


def show_saved(event) -> None:
    """Confirm that an event was created or updated."""
    support = event.support_contact.full_name if event.support_contact else "nobody yet"
    print_success(f"Event {event.id} saved: {event.name}, support: {support}.")

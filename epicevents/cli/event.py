"""Event commands."""

import click

from epicevents import auth, database
from epicevents.cli.console import print_info, print_table
from epicevents.cli.errors import handle_errors
from epicevents.repositories import EventRepository

COLUMNS = ("ID", "Name", "Client", "Start", "End", "Attendees", "Support")

DATE_FORMAT = "%Y-%m-%d %H:%M"


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
        event.support_contact.full_name if event.support_contact else "-",
    )


@click.group()
def event() -> None:
    """Events."""


@event.command("list")
@click.option(
    "--no-support", is_flag=True, help="Only the events with no support contact yet."
)
@click.option("--mine", is_flag=True, help="Only the events assigned to you.")
@handle_errors
def list_events(no_support: bool, mine: bool) -> None:
    """List the events."""
    with database.Session() as session:
        user = auth.get_current_user(session)
        repository = EventRepository(session)

        events = repository.list_filtered(
            no_support=no_support,
            support_contact_id=user.id if mine else None,
        )

        if not events:
            print_info("No event to display.")
            return

        print_table("Events", COLUMNS, [as_row(found) for found in events])

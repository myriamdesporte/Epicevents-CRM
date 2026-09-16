"""Event commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.repositories import EventRepository
from epicevents.services import auth
from epicevents.views import event as event_view


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
        current_user = auth.get_current_user(session)
        repository = EventRepository(session)

        events = repository.list_filtered(
            no_support=no_support,
            support_contact_id=current_user.id if mine else None,
        )

        event_view.show_events(events)

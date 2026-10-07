"""Event commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.controllers.guards import requires
from epicevents.controllers.options import ask, given
from epicevents.permissions import Permission
from epicevents.repositories import EventRepository, UserRepository
from epicevents.services import auth
from epicevents.services import event as event_service
from epicevents.validators import DATETIME_EXAMPLE, ValidationError
from epicevents.views import contract as contract_view
from epicevents.views import event as event_view
from epicevents.views import user as user_view


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

        event_view.show_list(events)


DATE_HELP = f"Local date and time, like '{DATETIME_EXAMPLE}'."


def _find(session, event_id: int):
    """Return the event, or explain that the id is unknown."""
    found = EventRepository(session).get(event_id)
    if found is None:
        raise ValidationError(f"No event has the id {event_id}.")
    return found


@event.command("create")
@requires(Permission.EVENT_CREATE)
@click.option("--contract-id", type=int)
@click.option("--name")
@click.option("--start", help=DATE_HELP)
@click.option("--end", help=DATE_HELP)
@click.option("--location")
@click.option("--attendees")
@click.option("--notes", default=None, help="Free text.")
@handle_errors
def create_event(
    contract_id: int,
    name: str,
    start: str,
    end: str,
    location: str,
    attendees: str,
    notes: str,
) -> None:
    """Create an event for a signed contract of one of your clients."""
    with database.Session() as session:
        current_user = auth.get_current_user(session)
        contract = event_service.contract_for_new_event(
            session, current_user, ask(contract_id, "Contract id", type=int)
        )
        contract_view.show_selected(contract)

    created = event_service.create_event(
        session,
        current_user,
        contract_id=contract.id,
        name=ask(name, "Event name"),
        start_date=ask(start, "Start"),
        end_date=ask(end, "End"),
        location=ask(location, "Location"),
        attendees=ask(attendees, "Attendees"),
        notes=notes,
    )
    event_view.show_saved(created)


@event.command("update")
@requires(Permission.EVENT_UPDATE)
@click.argument("event_id", type=int)
@click.option("--name")
@click.option("--start", help=DATE_HELP)
@click.option("--end", help=DATE_HELP)
@click.option("--location")
@click.option("--attendees")
@click.option("--notes")
@click.option(
    "--contract-id",
    type=int,
    help="Move the event to another signed contract. Management only.",
)
@handle_errors
def update_event(
    event_id: int,
    name: str,
    start: str,
    end: str,
    location: str,
    attendees: str,
    notes: str,
    contract_id: int,
) -> None:
    """Update an event, including the contract it belongs to."""
    changes = given(
        name=name,
        start_date=start,
        end_date=end,
        location=location,
        attendees=attendees,
        notes=notes,
        contract_id=contract_id,
    )

    if not changes:
        raise click.UsageError("Nothing to update: give at least one option.")

    with database.Session() as session:
        found = _find(session, event_id)
        event_view.show_selected(found)

        event_service.update_event(
            session, auth.get_current_user(session), found, **changes
        )
        event_view.show_saved(found)


@event.command("assign-support")
@requires(Permission.EVENT_UPDATE)
@click.argument("event_id", type=int)
@click.option("--user-id", type=int)
@handle_errors
def assign_support(event_id: int, user_id: int) -> None:
    """Assign a support collaborator to an event. Management only."""
    with database.Session() as session:
        found = _find(session, event_id)
        event_view.show_selected(found)

        user_id = ask(user_id, "Support collaborator id", type=int)

        support = UserRepository(session).get(user_id)
        if support is None:
            raise ValidationError(f"No collaborator has the id {user_id}.")

        user_view.show_selected(support)

        event_service.assign_support(
            session, auth.get_current_user(session), found, support
        )
        event_view.show_saved(found)


@event.command("show")
@click.argument("event_id", type=int)
@handle_errors
def show_event(event_id: int) -> None:
    """Show every field of one event, including location and notes."""
    with database.Session() as session:
        auth.get_current_user(session)
        event_view.show_details(_find(session, event_id))

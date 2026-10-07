"""Business rules about the events."""

from epicevents.models import RoleName
from epicevents.permissions import Permission
from epicevents.repositories import ContractRepository, EventRepository
from epicevents.services.auth import AuthorizationError, authorize
from epicevents.validators import (
    ValidationError,
    validate_attendees,
    validate_changes,
    validate_date_range,
    validate_required_text,
)

NAME_MAX = 150
LOCATION_MAX = 255

CHANGEABLE_FIELDS = {
    "name": lambda value: validate_required_text(
        value, field="Name", max_length=NAME_MAX
    ),
    "location": lambda value: validate_required_text(
        value, field="Location", max_length=LOCATION_MAX
    ),
    "attendees": validate_attendees,
    "notes": lambda value: value,
}


def _must_be_allowed_on(current_user, event) -> None:
    """Raise unless the collaborator may act on this event."""
    if current_user.role.name == RoleName.MANAGEMENT:
        return

    if event.support_contact_id != current_user.id:
        raise AuthorizationError(
            "This event is assigned to someone else: you can only update the "
            "events you are responsible for."
        )


def contract_for_new_event(session, current_user, contract_id):
    """Return the contract an event may be created for, or say why it may not."""
    authorize(current_user, Permission.EVENT_CREATE)

    contract = ContractRepository(session).get(contract_id)
    if contract is None:
        raise ValidationError(f"No contract has the id {contract_id}.")

    if contract.client.sales_contact_id != current_user.id:
        raise AuthorizationError(
            "This contract belongs to another collaborator's client: you can "
            "only create events for your own clients."
        )

    if not contract.is_signed:
        raise ValidationError(
            "This contract is not signed yet: an event can only be created once "
            "the client has signed."
        )

    if contract.event is not None:
        raise ValidationError("This contract already has an event.")

    return contract


def create_event(
    session,
    current_user,
    *,
    contract_id,
    name,
    start_date,
    end_date,
    location,
    attendees,
    notes=None,
):
    """Create an event for a signed contract of one of your own clients."""
    contract = contract_for_new_event(session, current_user, contract_id)

    start, end = validate_date_range(start_date, end_date)

    return EventRepository(session).add(
        contract_id=contract.id,
        name=validate_required_text(name, field="Name", max_length=NAME_MAX),
        start_date=start,
        end_date=end,
        location=validate_required_text(
            location, field="Location", max_length=LOCATION_MAX
        ),
        attendees=validate_attendees(attendees),
        notes=notes,
        # No support contact yet: management assigns one afterward.
        support_contact_id=None,
    )


def assign_support(session, current_user, event, support_user):
    """Assign a support collaborator to an event. Management only."""
    authorize(current_user, Permission.EVENT_UPDATE)

    if current_user.role.name != RoleName.MANAGEMENT:
        raise AuthorizationError(
            "Only the management department assigns a support contact."
        )

    if support_user.role.name != RoleName.SUPPORT:
        raise ValidationError(
            f"{support_user.full_name} is in the {support_user.role.name} "
            "department: only a support collaborator can be assigned to an event."
        )

    return EventRepository(session).update(event, support_contact_id=support_user.id)


def _moved_to_contract(session, current_user, event, contract_id) -> int:
    """Return the id of the contract an event is being moved to."""
    if current_user.role.name != RoleName.MANAGEMENT:
        raise AuthorizationError(
            "Only the management department can move an event to another " "contract."
        )

    contract = ContractRepository(session).get(contract_id)
    if contract is None:
        raise ValidationError(f"No contract has the id {contract_id}.")

    if not contract.is_signed:
        raise ValidationError(
            "This contract is not signed yet: an event can only belong to a "
            "signed contract."
        )

    # Moving an event onto its current contract is allowed.
    if contract.event is not None and contract.event.id != event.id:
        raise ValidationError("This contract already has an event.")

    return contract.id


def update_event(session, current_user, event, **changes):
    """Update an event, including the contract it belongs to."""
    authorize(current_user, Permission.EVENT_UPDATE)
    _must_be_allowed_on(current_user, event)

    if "contract_id" in changes:
        moved = {
            "contract_id": _moved_to_contract(
                session, current_user, event, changes.pop("contract_id")
            )
        }
    else:
        moved = {}

    if "start_date" in changes or "end_date" in changes:
        start, end = validate_date_range(
            changes.pop("start_date", event.start_date),
            changes.pop("end_date", event.end_date),
        )
        dates = {"start_date": start, "end_date": end}
    else:
        dates = {}

    validated = validate_changes(changes, CHANGEABLE_FIELDS)

    return EventRepository(session).update(event, **validated, **dates, **moved)

"""Business rules about the clients."""

from epicevents.permissions import Permission
from epicevents.repositories import ClientRepository
from epicevents.services.auth import AuthorizationError, authorize
from epicevents.validators import (
    validate_changes,
    validate_email,
    validate_phone,
    validate_required_text,
)

FULL_NAME_MAX = 100
COMPANY_NAME_MAX = 150

CHANGEABLE_FIELDS = {
    "full_name": lambda value: validate_required_text(
        value, field="Full name", max_length=FULL_NAME_MAX
    ),
    "email": validate_email,
    "phone": validate_phone,
    "company_name": lambda value: validate_required_text(
        value, field="Company name", max_length=COMPANY_NAME_MAX
    ),
}


def _must_be_the_sales_contact(current_user, client) -> None:
    """Raise unless the collaborator is the sales contact of this client."""
    if client.sales_contact_id != current_user.id:
        raise AuthorizationError(
            f"{client.full_name} is followed by another collaborator: you can "
            "only update your own clients."
        )


def create_client(session, current_user, *, full_name, email, phone, company_name):
    """Create a client, automatically assigned to the sales collaborator."""
    authorize(current_user, Permission.CLIENT_CREATE)

    return ClientRepository(session).add(
        full_name=validate_required_text(
            full_name, field="Full name", max_length=FULL_NAME_MAX
        ),
        email=validate_email(email),
        phone=validate_phone(phone),
        company_name=validate_required_text(
            company_name, field="Company name", max_length=COMPANY_NAME_MAX
        ),
        sales_contact_id=current_user.id,
    )


def update_client(session, current_user, client, **changes):
    """Update a client the collaborator is the sales contact of."""
    authorize(current_user, Permission.CLIENT_UPDATE)
    _must_be_the_sales_contact(current_user, client)

    validated = validate_changes(changes, CHANGEABLE_FIELDS)

    return ClientRepository(session).update(client, **validated)

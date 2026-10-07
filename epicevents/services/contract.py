"""Business rules about the contracts."""

from epicevents import monitoring
from epicevents.models import RoleName
from epicevents.permissions import Permission
from epicevents.repositories import ClientRepository, ContractRepository
from epicevents.services.auth import AuthorizationError, authorize
from epicevents.validators import (
    ValidationError,
    validate_amount,
    validate_amount_due,
)

CHANGEABLE_FIELDS = frozenset({"total_amount", "amount_due", "is_signed", "client_id"})


def _must_be_allowed_on(current_user, contract) -> None:
    """Raise unless the collaborator may act on this contract."""
    if current_user.role.name == RoleName.MANAGEMENT:
        return

    if contract.client.sales_contact_id != current_user.id:
        raise AuthorizationError(
            "This contract belongs to another collaborator's client: you can "
            "only update the contracts of your own clients."
        )


def client_for_new_contract(session, current_user, client_id):
    """Return the client a contract may be created for, or say why not."""
    authorize(current_user, Permission.CONTRACT_CREATE)

    client = ClientRepository(session).get(client_id)
    if client is None:
        raise ValidationError(f"No client has the id {client_id}.")

    return client


def create_contract(
    session, current_user, *, client_id, total_amount, amount_due, is_signed=False
):
    """Create a contract for a client. Management only."""
    client = client_for_new_contract(session, current_user, client_id)

    total = validate_amount(total_amount, field="Total amount")

    return ContractRepository(session).add(
        client_id=client.id,
        total_amount=total,
        amount_due=validate_amount_due(amount_due, total),
        is_signed=bool(is_signed),
    )


def _moved_to_client(session, current_user, client_id) -> int:
    """Return the id of the client a contract is being moved to."""
    if current_user.role.name != RoleName.MANAGEMENT:
        raise AuthorizationError(
            "Only the management department can move a contract to another " "client."
        )

    client = ClientRepository(session).get(client_id)
    if client is None:
        raise ValidationError(f"No client has the id {client_id}.")

    return client.id


def update_contract(session, current_user, contract, **changes):
    """Update a contract's amounts or signature."""
    authorize(current_user, Permission.CONTRACT_UPDATE)
    _must_be_allowed_on(current_user, contract)

    refused = set(changes) - CHANGEABLE_FIELDS
    if refused:
        raise ValidationError(f"Cannot be changed: {', '.join(sorted(refused))}.")

    total = validate_amount(
        changes.get("total_amount", contract.total_amount), field="Total amount"
    )
    validated = {
        "total_amount": total,
        "amount_due": validate_amount_due(
            changes.get("amount_due", contract.amount_due), total
        ),
    }

    if "is_signed" in changes:
        validated["is_signed"] = bool(changes["is_signed"])

    if "client_id" in changes:
        validated["client_id"] = _moved_to_client(
            session, current_user, changes["client_id"]
        )

    return ContractRepository(session).update(contract, **validated)


def sign_contract(session, current_user, contract):
    """Mark a contract as signed."""
    authorize(current_user, Permission.CONTRACT_UPDATE)
    _must_be_allowed_on(current_user, contract)

    if contract.is_signed:
        raise ValidationError("This contract is already signed.")

    signed = ContractRepository(session).update(contract, is_signed=True)
    monitoring.log_contract_signed(signed, current_user)
    return signed

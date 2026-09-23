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


def _must_be_allowed_on(current_user, contract) -> None:
    """Raise unless the collaborator may act on this contract."""
    if current_user.role.name == RoleName.MANAGEMENT:
        return

    if contract.client.sales_contact_id != current_user.id:
        raise AuthorizationError(
            "This contract belongs to another collaborator's client: you can "
            "only update the contracts of your own clients."
        )


def create_contract(
    session, current_user, *, client_id, total_amount, amount_due, is_signed=False
):
    """Create a contract for a client. Management only."""
    authorize(current_user, Permission.CONTRACT_CREATE)

    client = ClientRepository(session).get(client_id)
    if client is None:
        raise ValidationError(f"No client has the id {client_id}.")

    total = validate_amount(total_amount, field="Total amount")

    return ContractRepository(session).add(
        client_id=client.id,
        total_amount=total,
        amount_due=validate_amount_due(amount_due, total),
        is_signed=bool(is_signed),
    )


def update_contract(session, current_user, contract, **changes):
    """Update a contract's amounts or signature."""
    authorize(current_user, Permission.CONTRACT_UPDATE)
    _must_be_allowed_on(current_user, contract)

    refused = set(changes) - {"total_amount", "amount_due", "is_signed"}
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

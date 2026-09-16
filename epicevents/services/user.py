"""Business rules about the collaborators."""

from epicevents.permissions import Permission
from epicevents.repositories import ClientRepository, RoleRepository, UserRepository
from epicevents.security import hash_password
from epicevents.services.auth import authorize
from epicevents.validators import (
    ValidationError,
    validate_changes,
    validate_email,
    validate_password,
    validate_required_text,
    validate_role_name,
)

FULL_NAME_MAX = 100
EMPLOYEE_NUMBER_MAX = 20


def _validate_full_name(value):
    return validate_required_text(value, field="Full name", max_length=FULL_NAME_MAX)


def _validate_employee_number(value):
    return validate_required_text(
        value, field="Employee number", max_length=EMPLOYEE_NUMBER_MAX
    )


def _role_id(session, role_name: str) -> int:
    """Return the id of a role, refusing a name the database does not know."""
    repository = RoleRepository(session)
    name = validate_role_name(role_name, repository.names())
    return repository.get_by_name(name).id


def _refuse_duplicate(session, *, email=None, employee_number=None, allow=None):
    """Refuse an email or employee number already taken by someone else."""
    repository = UserRepository(session)

    if email is not None:
        existing = repository.get_by_email(email)
        if existing is not None and existing is not allow:
            raise ValidationError(f"The email {email} is already used.")

    if employee_number is not None:
        existing = repository.get_by_employee_number(employee_number)
        if existing is not None and existing is not allow:
            raise ValidationError(
                f"The employee number {employee_number} is already used."
            )


def create_user(
    session,
    current_user,
    *,
    employee_number,
    full_name,
    email,
    password,
    role_name,
):
    """Create a collaborator. Management only."""
    authorize(current_user, Permission.USER_CREATE)

    employee_number = _validate_employee_number(employee_number)
    email = validate_email(email)
    _refuse_duplicate(session, email=email, employee_number=employee_number)

    return UserRepository(session).add(
        employee_number=employee_number,
        full_name=_validate_full_name(full_name),
        email=email,
        # The plaintext password never reaches the repository.
        password_hash=hash_password(validate_password(password)),
        role_id=_role_id(session, role_name),
    )


def update_user(session, current_user, user, **changes):
    """Update a collaborator, including their department. Management only."""
    authorize(current_user, Permission.USER_UPDATE)

    computed = {}

    if "role_name" in changes:
        computed["role_id"] = _role_id(session, changes.pop("role_name"))

    if "password" in changes:
        computed["password_hash"] = hash_password(
            validate_password(changes.pop("password"))
        )

    validated = validate_changes(
        changes,
        {
            "employee_number": _validate_employee_number,
            "full_name": _validate_full_name,
            "email": validate_email,
        },
    )

    _refuse_duplicate(
        session,
        email=validated.get("email"),
        employee_number=validated.get("employee_number"),
        allow=user,
    )

    return UserRepository(session).update(user, **validated, **computed)


def delete_user(session, current_user, user) -> None:
    """Delete a collaborator, unless clients still depend on them."""
    authorize(current_user, Permission.USER_DELETE)

    clients = ClientRepository(session).list_for_sales_contact(user.id)
    if clients:
        raise ValidationError(
            f"{user.full_name} is still the sales contact of {len(clients)} "
            "client(s). Reassign them to another collaborator before deleting "
            "this account."
        )

    UserRepository(session).delete(user)

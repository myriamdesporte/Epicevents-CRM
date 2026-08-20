"""Role-based permissions for Epic Events CRM."""

import enum

from epicevents.models import RoleName


class Permission(enum.StrEnum):
    """An action a collaborator may be allowed to perform."""

    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    CLIENT_CREATE = "client_create"
    CLIENT_UPDATE = "client_update"

    CONTRACT_CREATE = "contract_create"
    CONTRACT_UPDATE = "contract_update"

    EVENT_CREATE = "event_create"
    EVENT_UPDATE = "event_update"


NO_PERMISSION: frozenset[Permission] = frozenset()

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    RoleName.MANAGEMENT: frozenset(
        {
            Permission.USER_CREATE,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.CONTRACT_CREATE,
            Permission.CONTRACT_UPDATE,
            Permission.EVENT_UPDATE,
        }
    ),
    RoleName.SALES: frozenset(
        {
            Permission.CLIENT_CREATE,
            Permission.CLIENT_UPDATE,
            Permission.CONTRACT_UPDATE,
            Permission.EVENT_CREATE,
        }
    ),
    RoleName.SUPPORT: frozenset(
        {
            Permission.EVENT_UPDATE,
        }
    ),
}


def permissions_for(role_name: str) -> frozenset[Permission]:
    """Return the permissions granted for a role_name."""

    return ROLE_PERMISSIONS.get(role_name, NO_PERMISSION)


def has_permission(role_name: str, permission: Permission) -> bool:
    """Tell whether the given role is allowed to perform the given action."""

    return permission in permissions_for(role_name)

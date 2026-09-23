"""Tests for the role-based permission matrix."""

from epicevents.models import RoleName
from epicevents.permissions import (
    ROLE_PERMISSIONS,
    Permission,
    has_permission,
    permissions_for,
)


def test_only_management_manages_collaborators():
    """Only the management department manages collaborators."""
    for permission in (
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
    ):
        assert has_permission(RoleName.MANAGEMENT, permission) is True
        assert has_permission(RoleName.SALES, permission) is False
        assert has_permission(RoleName.SUPPORT, permission) is False


def test_only_sales_manages_clients():
    """Only the sales department manages the client relationship."""
    for permission in (
        Permission.CLIENT_CREATE,
        Permission.CLIENT_UPDATE,
    ):
        assert has_permission(RoleName.SALES, permission) is True
        assert has_permission(RoleName.MANAGEMENT, permission) is False
        assert has_permission(RoleName.SUPPORT, permission) is False


def test_only_management_creates_contracts():
    """Only management commits the company to a contract."""
    assert has_permission(RoleName.MANAGEMENT, Permission.CONTRACT_CREATE) is True
    assert has_permission(RoleName.SALES, Permission.CONTRACT_CREATE) is False
    assert has_permission(RoleName.SUPPORT, Permission.CONTRACT_CREATE) is False


def test_contracts_are_updated_by_management_and_sales():
    """Same action, different scopes: management amends, sales negotiates."""
    assert has_permission(RoleName.MANAGEMENT, Permission.CONTRACT_UPDATE) is True
    assert has_permission(RoleName.SALES, Permission.CONTRACT_UPDATE) is True
    assert has_permission(RoleName.SUPPORT, Permission.CONTRACT_UPDATE) is False


def test_only_sales_creates_events():
    """Only sales schedules a new event, once a contract is signed."""
    assert has_permission(RoleName.SALES, Permission.EVENT_CREATE) is True
    assert has_permission(RoleName.MANAGEMENT, Permission.EVENT_CREATE) is False
    assert has_permission(RoleName.SUPPORT, Permission.EVENT_CREATE) is False


def test_events_are_updated_by_management_and_support():
    """Same action, different scopes: management assigns, support organises."""
    assert has_permission(RoleName.MANAGEMENT, Permission.EVENT_UPDATE) is True
    assert has_permission(RoleName.SUPPORT, Permission.EVENT_UPDATE) is True
    assert has_permission(RoleName.SALES, Permission.EVENT_UPDATE) is False


def test_support_only_updates_events():
    """Support has exactly one permission: updating events."""
    assert permissions_for(RoleName.SUPPORT) == frozenset({Permission.EVENT_UPDATE})


def test_unknown_role_gets_no_permission():
    """Denying by default: an unlisted role must never open access."""
    assert permissions_for("intern") == frozenset()
    assert has_permission("intern", Permission.USER_CREATE) is False


def test_every_role_has_permissions_defined():
    """Guard against adding a role to RoleName without granting it anything."""
    for role in RoleName:
        assert role in ROLE_PERMISSIONS

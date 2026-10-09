"""Tests for the business rules."""

from decimal import Decimal

import pytest

from epicevents.exceptions import AuthorizationError, ValidationError
from epicevents.models import RoleName
from epicevents.repositories import ClientRepository, EventRepository, UserRepository
from epicevents.services import client as client_service
from epicevents.services import contract as contract_service
from epicevents.services import event as event_service
from epicevents.services import user as user_service
from tests.conftest import PASSWORD, create_client, create_contract, create_event

# --------------------------------------------------------------------------
# Collaborators
# --------------------------------------------------------------------------


def test_management_creates_a_collaborator(session, management_user):
    """Test that management can create a collaborator with the specified role."""
    created = user_service.create_user(
        session,
        management_user,
        employee_number="EE-100",
        full_name="Nouvelle Recrue",
        email="recrue@epicevents.fr",
        password=PASSWORD,
        role_name=RoleName.SUPPORT,
    )

    assert created.id is not None
    assert created.role.name == RoleName.SUPPORT


def test_a_created_collaborator_can_log_in(session, management_user):
    """Test that a created collaborator can log in with the original password."""
    created = user_service.create_user(
        session,
        management_user,
        employee_number="EE-100",
        full_name="Nouvelle Recrue",
        email="recrue@epicevents.fr",
        password=PASSWORD,
        role_name=RoleName.SUPPORT,
    )

    assert created.password_hash != PASSWORD
    assert created.check_password(PASSWORD) is True


def test_sales_cannot_create_a_collaborator(session, sales_user):
    """Test that sales collaborators cannot create new collaborators."""
    with pytest.raises(AuthorizationError):
        user_service.create_user(
            session,
            sales_user,
            employee_number="EE-100",
            full_name="Nouvelle Recrue",
            email="recrue@epicevents.fr",
            password=PASSWORD,
            role_name=RoleName.SUPPORT,
        )


def test_a_duplicate_email_is_refused(session, management_user, sales_user):
    """Test that creating a collaborator with an existing email is refused."""
    with pytest.raises(ValidationError, match="already used"):
        user_service.create_user(
            session,
            management_user,
            employee_number="EE-100",
            full_name="Nouvelle Recrue",
            email=sales_user.email,
            password=PASSWORD,
            role_name=RoleName.SUPPORT,
        )


def test_an_unknown_role_is_refused(session, management_user):
    """Test that creating a collaborator with an unknown role is refused."""
    with pytest.raises(ValidationError, match="not a known role"):
        user_service.create_user(
            session,
            management_user,
            employee_number="EE-100",
            full_name="Nouvelle Recrue",
            email="recrue@epicevents.fr",
            password=PASSWORD,
            role_name="intern",
        )


def test_management_changes_the_department_of_a_collaborator(
    session, management_user, sales_user
):
    """Test that management can change a collaborator's department."""
    user_service.update_user(session, management_user, sales_user, role_name="support")

    assert sales_user.role.name == RoleName.SUPPORT


def test_a_collaborator_can_keep_their_own_email_when_updated(
    session, management_user, sales_user
):
    """Test that a collaborator can keep their email address when updated."""
    user_service.update_user(
        session,
        management_user,
        sales_user,
        email=sales_user.email,
        full_name="Bill B.",
    )

    assert sales_user.full_name == "Bill B."


def test_the_password_hash_cannot_be_set_directly(session, management_user, sales_user):
    """Test that a collaborator's password hash cannot be set directly."""
    with pytest.raises(ValidationError, match="Cannot be changed"):
        user_service.update_user(
            session, management_user, sales_user, password_hash="whatever"
        )


def test_the_role_id_cannot_be_set_directly(session, management_user, sales_user):
    """Test that a collaborator's role ID cannot be set directly."""
    with pytest.raises(ValidationError, match="Cannot be changed"):
        user_service.update_user(session, management_user, sales_user, role_id=2)


def test_updating_the_password_actually_hashes_it(session, management_user, sales_user):
    """Test that updating a collaborator's password hashes it correctly."""
    user_service.update_user(
        session, management_user, sales_user, password="UnAutreMotDePasse42!"
    )

    assert sales_user.check_password("UnAutreMotDePasse42!") is True


def test_deleting_a_collaborator_who_still_has_clients_is_refused(
    session, management_user, sales_user, client
):
    """Test that deleting a collaborator with assigned clients is refused."""
    with pytest.raises(ValidationError, match="Reassign them"):
        user_service.delete_user(session, management_user, sales_user)


def test_a_collaborator_without_clients_is_deleted(
    session, management_user, support_user
):
    """Test that a collaborator without assigned clients can be deleted."""
    support_id = support_user.id

    user_service.delete_user(session, management_user, support_user)

    assert UserRepository(session).get(support_id) is None


def test_deleting_a_support_collaborator_unassigns_their_events(
    session, management_user, support_user, signed_contract
):
    """Test that deleting a support collaborator unassigns their events."""
    event = create_event(session, signed_contract, support_user)
    event_id = event.id

    user_service.delete_user(session, management_user, support_user)
    session.expire_all()

    found = EventRepository(session).get(event_id)
    assert found is not None
    assert found.support_contact_id is None


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------


def test_a_created_client_is_assigned_to_its_creator(session, sales_user):
    """Test that a new client is assigned to its creator."""
    created = client_service.create_client(
        session,
        sales_user,
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+678 123 456 78",
        company_name="Cool Startup LLC",
    )

    assert created.sales_contact_id == sales_user.id


def test_support_cannot_create_a_client(session, support_user):
    """Test that support collaborators cannot create clients."""
    with pytest.raises(AuthorizationError):
        client_service.create_client(
            session,
            support_user,
            full_name="Kevin Casey",
            email="kevin@startup.io",
            phone="+678 123 456 78",
            company_name="Cool Startup LLC",
        )


def test_a_malformed_email_is_refused(session, sales_user):
    """Test that an invalid email address is rejected."""
    with pytest.raises(ValidationError, match="not a valid email"):
        client_service.create_client(
            session,
            sales_user,
            full_name="Kevin Casey",
            email="kevin-at-startup",
            phone="+678 123 456 78",
            company_name="Cool Startup LLC",
        )


def test_a_sales_collaborator_updates_their_own_client(session, sales_user, client):
    """Test that sales collaborators can update their own clients."""
    client_service.update_client(session, sales_user, client, phone="+33 6 12 34 56 78")

    assert client.phone == "+33 6 12 34 56 78"


def test_a_sales_collaborator_cannot_update_someone_elses_client(
    session, sales_user, management_user
):
    """Test that sales collaborators cannot update other collaborators' clients."""
    other = create_client(session, management_user, full_name="Lou Bouzin")

    with pytest.raises(AuthorizationError, match="only update your own clients"):
        client_service.update_client(session, sales_user, other, phone="+33 6 00 00 00")


def test_a_client_cannot_be_reassigned_through_an_update(
    session, sales_user, management_user, client
):
    """Test that a client's sales contact cannot be changed directly."""
    with pytest.raises(ValidationError, match="Cannot be changed"):
        client_service.update_client(
            session, sales_user, client, sales_contact_id=management_user.id
        )


# --------------------------------------------------------------------------
# Contracts
# --------------------------------------------------------------------------


def test_management_creates_a_contract(session, management_user, client):
    """Test that management can create a contract."""
    created = contract_service.create_contract(
        session,
        management_user,
        client_id=client.id,
        total_amount="1000.00",
        amount_due="400.00",
    )

    assert created.total_amount == Decimal("1000.00")
    assert created.is_signed is False


def test_sales_cannot_create_a_contract(session, sales_user, client):
    """Test that sales collaborators cannot create contracts."""
    with pytest.raises(AuthorizationError):
        contract_service.create_contract(
            session,
            sales_user,
            client_id=client.id,
            total_amount="1000.00",
            amount_due="400.00",
        )


def test_an_amount_due_above_the_total_is_refused(session, management_user, client):
    """Test that the amount due cannot exceed the total amount."""
    with pytest.raises(ValidationError, match="cannot exceed"):
        contract_service.create_contract(
            session,
            management_user,
            client_id=client.id,
            total_amount="1000.00",
            amount_due="1500.00",
        )


def test_sales_updates_the_contract_of_their_own_client(
    session, sales_user, signed_contract
):
    """Test that sales can update contracts belonging to their own clients."""
    contract_service.update_contract(
        session, sales_user, signed_contract, amount_due="0.00"
    )

    assert signed_contract.amount_due == Decimal("0.00")


def test_sales_cannot_update_the_contract_of_another_client(
    session, sales_user, management_user
):
    """Test that sales cannot update contracts belonging to other clients."""
    other_client = create_client(session, management_user, full_name="Lou Bouzin")
    other_contract = create_contract(session, other_client)

    with pytest.raises(AuthorizationError, match="only update the contracts"):
        contract_service.update_contract(
            session, sales_user, other_contract, amount_due="0.00"
        )


def test_lowering_the_total_below_the_amount_due_is_refused(
    session, management_user, client
):
    """Test that the total amount cannot be lower than the amount due."""
    contract = create_contract(
        session, client, total=Decimal("1000.00"), due=Decimal("900.00")
    )

    with pytest.raises(ValidationError, match="cannot exceed"):
        contract_service.update_contract(
            session, management_user, contract, total_amount="500.00"
        )


def test_signing_a_contract(session, management_user, client):
    """Test that management can sign a contract."""
    contract = create_contract(session, client, signed=False)

    contract_service.sign_contract(session, management_user, contract)

    assert contract.is_signed is True


def test_signing_twice_is_refused(session, management_user, signed_contract):
    """Test that a contract cannot be signed twice."""
    with pytest.raises(ValidationError, match="already signed"):
        contract_service.sign_contract(session, management_user, signed_contract)


@pytest.fixture
def signatures(monkeypatch):
    """Record the contract signatures sent to Sentry."""
    logged = []
    monkeypatch.setattr(
        contract_service.monitoring,
        "log_contract_signed",
        lambda contract, by: logged.append((contract.id, by.employee_number)),
    )
    return logged


def test_signing_a_contract_is_logged(session, management_user, client, signatures):
    """Test that signing a contract is logged."""
    contract = create_contract(session, client, signed=False)

    contract_service.sign_contract(session, management_user, contract)

    assert signatures == [(contract.id, management_user.employee_number)]


def test_a_contract_created_signed_is_logged(
    session, management_user, client, signatures
):
    """Test that creating a signed contract is logged."""
    created = contract_service.create_contract(
        session,
        management_user,
        client_id=client.id,
        total_amount="1000.00",
        amount_due="400.00",
        is_signed=True,
    )

    assert signatures == [(created.id, management_user.employee_number)]


def test_an_unsigned_contract_created_is_not_logged(
    session, management_user, client, signatures
):
    """Test that creating an unsigned contract is not logged as signed."""
    contract_service.create_contract(
        session,
        management_user,
        client_id=client.id,
        total_amount="1000.00",
        amount_due="400.00",
    )

    assert signatures == []


def test_signing_through_an_update_is_logged(
    session, management_user, client, signatures
):
    """Test that signing a contract through an update is logged."""
    contract = create_contract(session, client, signed=False)

    contract_service.update_contract(session, management_user, contract, is_signed=True)

    assert signatures == [(contract.id, management_user.employee_number)]


def test_updating_the_amounts_of_a_signed_contract_is_not_logged(
    session, management_user, signed_contract, signatures
):
    """Test that updating a signed contract's amounts does not log a new signature."""
    contract_service.update_contract(
        session, management_user, signed_contract, amount_due="0.00"
    )

    assert signatures == []


def test_a_signed_contract_cannot_be_unsigned(
    session, management_user, signed_contract
):
    """Test that a signed contract cannot be unsigned."""
    with pytest.raises(ValidationError, match="cannot be unsigned"):
        contract_service.update_contract(
            session, management_user, signed_contract, is_signed=False
        )


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------


def _event_fields(**overrides):
    fields = {
        "name": "John Ouick Wedding",
        "start_date": "2026-06-04 13:00",
        "end_date": "2026-06-05 02:00",
        "location": "53 Rue du Chateau, Cande-sur-Beuvron",
        "attendees": "75",
    }
    fields.update(overrides)
    return fields


def test_sales_creates_an_event_for_a_signed_contract(
    session, sales_user, signed_contract
):
    """Test that sales can create an event for a signed contract."""
    created = event_service.create_event(
        session, sales_user, contract_id=signed_contract.id, **_event_fields()
    )

    assert created.id is not None
    assert created.support_contact_id is None


def test_an_event_needs_a_signed_contract(session, sales_user, client):
    """Test that an event cannot be created for an unsigned contract."""
    unsigned = create_contract(session, client, signed=False)

    with pytest.raises(ValidationError, match="not signed yet"):
        event_service.create_event(
            session, sales_user, contract_id=unsigned.id, **_event_fields()
        )


def test_an_event_can_only_be_created_for_your_own_client(
    session, sales_user, management_user
):
    """Test that sales can only create events for their own clients."""
    other_client = create_client(session, management_user, full_name="Lou Bouzin")
    other_contract = create_contract(session, other_client)

    with pytest.raises(AuthorizationError, match="your own clients"):
        event_service.create_event(
            session, sales_user, contract_id=other_contract.id, **_event_fields()
        )


def test_a_contract_cannot_have_two_events(session, sales_user, signed_contract):
    """Test that a contract can have only one event."""
    event_service.create_event(
        session, sales_user, contract_id=signed_contract.id, **_event_fields()
    )

    with pytest.raises(ValidationError, match="already has an event"):
        event_service.create_event(
            session, sales_user, contract_id=signed_contract.id, **_event_fields()
        )


def test_an_end_before_the_start_is_refused(session, sales_user, signed_contract):
    """Test that an event cannot end before it starts."""
    with pytest.raises(ValidationError, match="after its beginning"):
        event_service.create_event(
            session,
            sales_user,
            contract_id=signed_contract.id,
            **_event_fields(end_date="2026-06-03 02:00"),
        )


def test_management_assigns_a_support_collaborator(
    session, management_user, support_user, signed_contract
):
    """Test that management can assign a support collaborator to an event."""
    event = create_event(session, signed_contract, None)

    event_service.assign_support(session, management_user, event, support_user)

    assert event.support_contact_id == support_user.id


def test_a_sales_collaborator_cannot_be_assigned_as_support(
    session, management_user, sales_user, signed_contract
):
    """Test that only support collaborators can be assigned to events."""
    event = create_event(session, signed_contract, None)

    with pytest.raises(ValidationError, match="only a support collaborator"):
        event_service.assign_support(session, management_user, event, sales_user)


def test_support_updates_the_event_assigned_to_them(
    session, support_user, signed_contract
):
    """Test that support can update an event assigned to them."""
    event = create_event(session, signed_contract, support_user)

    event_service.update_event(session, support_user, event, attendees="200")

    assert event.attendees == 200


def test_support_cannot_update_an_event_of_someone_else(
    session, support_user, signed_contract
):
    """Test that support cannot update an unassigned event."""
    event = create_event(session, signed_contract, None)

    with pytest.raises(AuthorizationError, match="events you are responsible for"):
        event_service.update_event(session, support_user, event, attendees="200")


def test_support_cannot_reassign_the_event_to_themselves(
    session, support_user, signed_contract
):
    """Test that support cannot assign events directly."""
    event = create_event(session, signed_contract, support_user)

    with pytest.raises(ValidationError, match="Cannot be changed"):
        event_service.update_event(
            session, support_user, event, support_contact_id=support_user.id
        )


def test_management_updates_any_event(session, management_user, signed_contract):
    """Test that management can update any event."""
    event = create_event(session, signed_contract, None)

    event_service.update_event(session, management_user, event, name="Renamed")

    assert event.name == "Renamed"


def test_the_dates_of_an_event_can_be_moved(session, support_user, signed_contract):
    """Test that an event's dates can be updated."""
    event = create_event(session, signed_contract, support_user)

    event_service.update_event(
        session,
        support_user,
        event,
        start_date="2026-07-01 09:00",
        end_date="2026-07-01 18:00",
    )

    assert event.start_date < event.end_date


def test_moving_the_end_before_the_start_is_refused(
    session, support_user, signed_contract
):
    """Test that updating an event cannot make its end precede its start."""
    event = create_event(session, signed_contract, support_user)

    with pytest.raises(ValidationError, match="after its beginning"):
        event_service.update_event(
            session, support_user, event, end_date="2020-01-01 00:00"
        )


def test_an_event_needs_an_existing_contract(session, sales_user):
    """Test that an event cannot reference a nonexistent contract."""
    with pytest.raises(ValidationError, match="No contract has the id"):
        event_service.create_event(
            session, sales_user, contract_id=999, **_event_fields()
        )


def test_support_cannot_assign_a_support_contact(
    session, support_user, signed_contract
):
    """Test that only management can assign a support contact."""
    event = create_event(session, signed_contract, support_user)

    with pytest.raises(AuthorizationError, match="event_assign_support"):
        event_service.assign_support(session, support_user, event, support_user)


def test_a_contract_needs_an_existing_client(session, management_user):
    """Test that a contract cannot reference a nonexistent client."""
    with pytest.raises(ValidationError, match="No client has the id"):
        contract_service.create_contract(
            session,
            management_user,
            client_id=999,
            total_amount="1000.00",
            amount_due="0.00",
        )


def test_management_moves_a_contract_to_another_client(
    session, management_user, sales_user, signed_contract
):
    """Test that management can change a contract's client."""
    other = create_client(session, sales_user, full_name="Lou Bouzin")

    contract_service.update_contract(
        session, management_user, signed_contract, client_id=other.id
    )

    assert signed_contract.client_id == other.id


def test_moving_a_contract_to_an_unknown_client_is_refused(
    session, management_user, signed_contract
):
    """Test that a contract cannot be assigned to a nonexistent client."""
    with pytest.raises(ValidationError, match="No client has the id 999"):
        contract_service.update_contract(
            session, management_user, signed_contract, client_id=999
        )


def test_sales_cannot_move_a_contract_to_another_client(
    session, sales_user, signed_contract
):
    """Test that only management can change a contract's client."""
    with pytest.raises(AuthorizationError, match="management department"):
        contract_service.update_contract(
            session, sales_user, signed_contract, client_id=1
        )


def test_management_moves_an_event_to_another_contract(
    session, management_user, sales_user, client, signed_contract
):
    """Test that management can change an event's contract."""
    event = create_event(session, signed_contract, None)
    target = create_contract(session, client, signed=True)

    event_service.update_event(session, management_user, event, contract_id=target.id)

    assert event.contract_id == target.id


def test_moving_an_event_onto_a_taken_contract_is_refused(
    session, management_user, client, signed_contract
):
    """Test that an event cannot be moved to a contract that already has an event."""
    event = create_event(session, signed_contract, None)
    taken = create_contract(session, client, signed=True)
    create_event(session, taken, None, name="Already there")

    with pytest.raises(ValidationError, match="already has an event"):
        event_service.update_event(
            session, management_user, event, contract_id=taken.id
        )


def test_support_cannot_move_an_event_to_another_contract(
    session, support_user, client, signed_contract
):
    """Test that support cannot change an event's contract."""
    with pytest.raises(AuthorizationError, match="management department"):
        event = create_event(session, signed_contract, support_user)
        event_service.update_event(session, support_user, event, contract_id=1)


def test_a_contract_can_be_signed_through_an_update(session, management_user, client):
    """Test that management can sign a contract through an update."""
    contract = create_contract(session, client, signed=False)

    contract_service.update_contract(session, management_user, contract, is_signed=True)

    assert contract.is_signed is True


def test_a_duplicate_employee_number_is_refused(session, management_user, sales_user):
    """Test that an employee number cannot be used twice."""
    with pytest.raises(ValidationError, match="employee number"):
        user_service.create_user(
            session,
            management_user,
            employee_number=sales_user.employee_number,
            full_name="Nouvelle Recrue",
            email="recrue@epicevents.fr",
            password=PASSWORD,
            role_name=RoleName.SUPPORT,
        )


def test_every_collaborator_still_reads_every_client(session, support_user, client):
    """Test that all collaborators can view every client."""
    assert len(ClientRepository(session).list_all()) == 1

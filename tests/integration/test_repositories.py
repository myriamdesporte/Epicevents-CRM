"""Tests for the data access layer."""

from decimal import Decimal


import pytest
from sqlalchemy.exc import IntegrityError

from epicevents.repositories import (
    ClientRepository,
    ContractRepository,
    EventRepository,
    UserRepository,
)
from tests.conftest import create_client, create_contract, create_event

# --------------------------------------------------------------------------
# Collaborators
# --------------------------------------------------------------------------


def test_list_all_users(session, sales_user, management_user):
    """list_all returns every collaborator."""
    users = UserRepository(session).list_all()

    assert [user.id for user in users] == [sales_user.id, management_user.id]


def test_get_user_by_email(session, sales_user):
    """get_by_email returns the matching collaborator."""
    assert UserRepository(session).get_by_email(sales_user.email) is sales_user


def test_get_user_by_unknown_email_returns_none(session, sales_user):
    """get_by_email returns None when no collaborator has this email."""
    assert UserRepository(session).get_by_email("nobody@epicevents.fr") is None


def test_get_user_by_unknown_id_returns_none(session):
    """get returns None when no collaborator has this id."""
    assert UserRepository(session).get(999) is None


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------


def test_every_collaborator_can_read_every_client(session, sales_user, support_user):
    """Read access is granted to all."""
    create_client(session, sales_user, full_name="Kevin Casey")
    create_client(session, sales_user, full_name="Lou Bouzin")

    assert len(ClientRepository(session).list_all()) == 2


def test_list_clients_of_one_sales_contact(session, sales_user, management_user):
    """list_for_sales_contact returns only that sales contact's clients."""
    mine = create_client(session, sales_user, full_name="Kevin Casey")
    create_client(session, management_user, full_name="Lou Bouzin")

    clients = ClientRepository(session).list_for_sales_contact(sales_user.id)

    assert [client.id for client in clients] == [mine.id]


def test_client_carries_its_sales_contact(session, client, sales_user):
    """A client loaded by get() has its sales contact attached."""
    found = ClientRepository(session).get(client.id)

    assert found.sales_contact.email == sales_user.email


# --------------------------------------------------------------------------
# Contracts
# --------------------------------------------------------------------------


def test_list_unsigned_contracts(session, client):
    """list_unsigned returns only contracts that are not yet signed."""
    create_contract(session, client, signed=True)
    unsigned = create_contract(session, client, signed=False)

    contracts = ContractRepository(session).list_unsigned()

    assert [contract.id for contract in contracts] == [unsigned.id]


def test_list_contracts_not_fully_paid(session, client):
    """list_not_fully_paid returns only contracts with a remaining amount due."""
    create_contract(session, client, due=Decimal("0.00"))
    owing = create_contract(session, client, due=Decimal("250.00"))

    contracts = ContractRepository(session).list_not_fully_paid()

    assert [contract.id for contract in contracts] == [owing.id]


def test_list_contracts_of_one_sales_contact(session, sales_user, management_user):
    """list_for_sales_contact returns only contracts whose client belongs to that sales contact."""
    my_client = create_client(session, sales_user, full_name="Kevin Casey")
    other_client = create_client(session, management_user, full_name="Lou Bouzin")
    mine = create_contract(session, my_client)
    create_contract(session, other_client)

    contracts = ContractRepository(session).list_for_sales_contact(sales_user.id)

    assert [contract.id for contract in contracts] == [mine.id]


def test_contract_reaches_the_sales_contact_through_its_client(
    session, signed_contract, sales_user
):
    """A contract loaded by get() reaches its sales contact through its client."""
    found = ContractRepository(session).get(signed_contract.id)

    assert found.client.sales_contact.email == sales_user.email


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------


def test_list_events_without_support(session, client, support_user):
    """list_without_support returns only events with no support contact."""
    assigned_contract = create_contract(session, client)
    orphan_contract = create_contract(session, client)
    create_event(session, assigned_contract, support_user, name="Assigned")
    orphan = create_event(session, orphan_contract, None, name="Orphan")

    events = EventRepository(session).list_without_support()

    assert [event.id for event in events] == [orphan.id]


def test_list_events_of_one_support_contact(session, client, support_user):
    """list_for_support_contact returns only that support contact's events."""
    mine = create_event(session, create_contract(session, client), support_user)
    create_event(session, create_contract(session, client), None, name="Orphan")

    events = EventRepository(session).list_for_support_contact(support_user.id)

    assert [event.id for event in events] == [mine.id]


def test_event_without_support_has_no_support_contact(session, signed_contract):
    """An event loaded by get() has support_contact set to None when unassigned."""
    event = create_event(session, signed_contract, None)

    found = EventRepository(session).get(event.id)

    assert found.support_contact is None


def test_event_carries_its_contract_and_client(session, signed_contract, client):
    """An event loaded by get() reaches its client through its contract."""
    event = create_event(session, signed_contract, None)

    found = EventRepository(session).get(event.id)

    assert found.contract.client.full_name == client.full_name


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def test_add_saves_the_object(session, sales_user):
    """Creates the object and makes it retrievable from the database."""
    repository = ClientRepository(session)

    created = repository.add(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+678 123 456 78",
        company_name="Cool Startup LLC",
        sales_contact_id=sales_user.id,
    )

    assert created.id is not None
    assert repository.get(created.id).full_name == "Kevin Casey"


def test_add_refuses_a_field_that_is_not_a_column(session, sales_user):
    """Refuses unknown fields when creating an object."""
    with pytest.raises(TypeError):
        ClientRepository(session).add(
            full_name="Kevin Casey",
            phonee="+678 123 456 78",
            sales_contact_id=sales_user.id,
        )


def test_update_changes_only_the_given_fields(session, client):
    """Updates only the fields explicitly provided."""
    repository = ClientRepository(session)
    company_before = client.company_name

    repository.update(client, phone="+33 6 12 34 56 78")

    assert client.phone == "+33 6 12 34 56 78"
    assert client.company_name == company_before


def test_update_refuses_a_field_that_is_not_a_column(session, client):
    """Refuses unknown fields when updating an existing object."""
    with pytest.raises(ValueError, match="phonee"):
        ClientRepository(session).update(client, phonee="+33 6 12 34 56 78")


@pytest.mark.parametrize("field", ["id", "created_at", "updated_at"])
def test_update_refuses_the_protected_fields(session, client, field):
    """Refuses fields that must be managed automatically or remain unchanged."""
    with pytest.raises(ValueError, match=field):
        ClientRepository(session).update(client, **{field: 1})


def test_update_refreshes_the_last_update_date(session, client):
    """Automatically updates the last modification date."""
    before = client.updated_at

    ClientRepository(session).update(client, phone="+33 6 12 34 56 78")

    assert client.updated_at > before


def test_delete_removes_the_object(session, signed_contract):
    """Deletes the object from the database."""
    repository = ContractRepository(session)
    contract_id = signed_contract.id

    repository.delete(signed_contract)

    assert repository.get(contract_id) is None


def test_delete_is_refused_while_another_row_points_at_it(session, sales_user, client):
    """Refuses deletion when another object still references it."""
    with pytest.raises(IntegrityError):
        UserRepository(session).delete(sales_user)

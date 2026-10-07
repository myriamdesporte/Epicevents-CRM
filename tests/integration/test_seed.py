"""Tests for the demonstration dataset."""

from epicevents.models import Client, Contract, Event, RoleName, User
from seed_demo_data import CONTRACTS, EVENTS, already_filled, seed, wipe

PASSWORD = "MyPasswordDemo42!"


def test_the_dataset_is_accepted_by_the_services(session, management_user):
    """The dataset is accepted by the application."""
    seed(session, management_user, PASSWORD)

    assert session.query(User).count() == 5
    assert session.query(Client).count() == 3
    assert session.query(Contract).count() == len(CONTRACTS)
    assert session.query(Event).count() == len(EVENTS)


def test_every_filter_of_the_application_has_something_to_show(
    session, management_user
):
    """The dataset covers every application filter."""
    seed(session, management_user, PASSWORD)

    contracts = session.query(Contract).all()
    assert any(not c.is_signed for c in contracts), "contract list --unsigned"
    assert any(c.amount_due > 0 for c in contracts), "contract list --unpaid"
    assert any(c.amount_due == 0 for c in contracts), "and some fully paid"

    events = session.query(Event).all()
    assert any(e.support_contact is None for e in events), "event list --no-support"
    assert any(e.support_contact is not None for e in events), "and some assigned"


def test_two_sales_collaborators_follow_different_clients(session, management_user):
    """Two sales collaborators follow different clients."""
    seed(session, management_user, PASSWORD)

    contacts = {client.sales_contact_id for client in session.query(Client)}
    assert len(contacts) == 2


def test_running_it_twice_is_refused_then_allowed_by_a_reset(session, management_user):
    """A dataset can be reset and recreated."""
    seed(session, management_user, PASSWORD)
    assert already_filled(session) is True

    wipe(session, keep=management_user)

    assert already_filled(session) is False
    assert session.query(User).count() == 1
    assert session.query(Event).count() == 0

    seed(session, management_user, PASSWORD)
    assert session.query(Client).count() == 3


def test_the_support_collaborators_are_support(session, management_user):
    """Assigned event contacts have the support role."""
    seed(session, management_user, PASSWORD)

    assigned = [e.support_contact for e in session.query(Event) if e.support_contact]
    assert all(user.role.name == RoleName.SUPPORT for user in assigned)

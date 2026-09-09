"""Fixtures shared by the test suite."""

from datetime import timezone, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from epicevents import auth, database
from epicevents.database import Base
from epicevents.models import Role, RoleName, User, Contract, Event, Client

PASSWORD = "DummyPassword42!"


@pytest.fixture
def engine():
    """Create a fresh in-memory test database with the three roles already in it."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with sessionmaker(bind=engine)() as session:
        for role_name in RoleName:
            session.add(Role(name=role_name))
        session.commit()

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session(engine):
    """Give a test a session to read and write in the test database."""
    with sessionmaker(bind=engine)() as session:
        yield session


@pytest.fixture
def cli_database(engine, monkeypatch):
    """Make the CLI commands use the test database instead of the real one."""
    monkeypatch.setattr(database, "Session", sessionmaker(bind=engine))


def create_user(
    session, role_name: str, email: str, employee_number: str, full_name: str
) -> User:
    """Add a collaborator with the shared test password and return it."""
    role = session.scalar(select(Role).where(Role.name == role_name))
    user = User(
        employee_number=employee_number,
        full_name=full_name,
        email=email,
        role_id=role.id,
    )
    user.set_password(PASSWORD)
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def sales_user(session):
    """A collaborator from the sales department."""
    return create_user(
        session, RoleName.SALES, "bill@epicevents.fr", "EE-001", "Bill Sales"
    )


@pytest.fixture
def support_user(session):
    """A collaborator from the support department."""
    return create_user(
        session, RoleName.SUPPORT, "kate@epicevents.fr", "EE-002", "Kate Support"
    )


@pytest.fixture
def management_user(session):
    """A collaborator from the management department."""
    return create_user(
        session,
        RoleName.MANAGEMENT,
        "albert@epicevents.fr",
        "EE-003",
        "Albert Management",
    )


def create_client(session, sales_contact, full_name="Kevin Casey") -> Client:
    """Add a client followed by the given sales collaborator."""
    client = Client(
        full_name=full_name,
        email=f"{full_name.split()[0].lower()}@startup.io",
        phone="+678 123 456 78",
        company_name="Cool Startup LLC",
        sales_contact_id=sales_contact.id,
    )
    session.add(client)
    session.commit()
    return client


def create_contract(
    session, client, total=Decimal("1000.00"), due=Decimal("400.00"), signed=True
) -> Contract:
    """Add a contract for the given client."""
    contract = Contract(
        total_amount=total,
        amount_due=due,
        is_signed=signed,
        client_id=client.id,
    )
    session.add(contract)
    session.commit()
    return contract


def create_event(session, contract, support_contact=None, name="Wedding") -> Event:
    """Add an event for the given contract, with or without a support contact."""
    event = Event(
        name=name,
        start_date=datetime(2026, 6, 4, 13, 0, tzinfo=timezone.utc),
        end_date=datetime(2026, 6, 5, 2, 0, tzinfo=timezone.utc),
        location="53 Rue du Chateau, Cande-sur-Beuvron",
        attendees=75,
        notes=None,
        contract_id=contract.id,
        support_contact_id=support_contact.id if support_contact else None,
    )
    session.add(event)
    session.commit()
    return event


@pytest.fixture
def client(session, sales_user):
    """A client followed by the sales collaborator."""
    return create_client(session, sales_user)


@pytest.fixture
def signed_contract(session, client):
    """A signed contract, partially paid."""
    return create_contract(session, client)


@pytest.fixture(autouse=True)
def test_secret(monkeypatch):
    """Sign the test tokens with a throwaway secret, never the real one."""
    monkeypatch.setattr(auth, "JWT_SECRET", "fake-jwt-secret-for-testing-purposes-only")


@pytest.fixture(autouse=True)
def test_token_path(tmp_path, monkeypatch):
    """Redirect the token file into a temporary directory."""
    monkeypatch.setattr(auth, "TOKEN_PATH", tmp_path / ".epicevents" / "token")

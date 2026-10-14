"""Tests showing that personal data is encrypted in the database."""

import base64

import pytest
from click.testing import CliRunner
from sqlalchemy import Text, select, type_coerce
from sqlalchemy.exc import IntegrityError

from epicevents import config
from epicevents.controllers.main import cli
from epicevents.exceptions import ConfigurationError
from epicevents.models import Client, Event, User
from epicevents.repositories import ClientRepository, UserRepository
from tests.conftest import PASSWORD, create_event

OTHER_KEY = base64.urlsafe_b64encode(b"o" * 64).decode()


def stored(session, model, column, row_id):
    """Return the value exactly as the database stores it, without decrypting."""
    table = model.__table__
    query = select(type_coerce(table.c[column], Text)).where(table.c.id == row_id)
    return session.scalar(query)


def test_a_client_is_unreadable_in_the_database(session, client):
    """Name, email, phone and company are stored encrypted."""
    for column in ("full_name", "email", "phone", "company_name"):
        assert stored(session, Client, column, client.id) != getattr(client, column)


def test_the_application_reads_the_client_in_clear(session, client):
    """Decryption is automatic: the application sees the original text."""
    session.expire_all()

    found = ClientRepository(session).get(client.id)

    assert found.full_name == "Kevin Casey"


def test_a_collaborator_email_is_unreadable_in_the_database(session, sales_user):
    assert stored(session, User, "email", sales_user.id) != sales_user.email
    assert stored(session, User, "full_name", sales_user.id) != (sales_user.full_name)


def test_event_details_are_unreadable_in_the_database(
    session, signed_contract, support_user
):
    event = create_event(session, signed_contract, support_user)
    event.notes = "Kate needs to organize the DJ."
    session.commit()

    for column in ("name", "location", "notes"):
        assert stored(session, Event, column, event.id) != getattr(event, column)


def test_a_collaborator_is_still_found_by_email(session, sales_user):
    """Deterministic encryption: the searched email is encrypted the same way."""
    session.expire_all()

    assert UserRepository(session).get_by_email(sales_user.email).id == sales_user.id


def test_an_email_is_still_unique(session, sales_user):
    """Two identical emails give two identical encrypted values: refused."""
    duplicate = User(
        employee_number="EE-999",
        full_name="Someone Else",
        email=sales_user.email,
        password_hash="x",
        role_id=sales_user.role_id,
    )
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()


def test_a_missing_key_is_reported(session, client, monkeypatch):
    monkeypatch.setattr(config, "ENCRYPTION_KEY", None)
    session.expire_all()

    with pytest.raises(ConfigurationError, match="ENCRYPTION_KEY is missing"):
        ClientRepository(session).get(client.id).full_name


def test_a_malformed_key_is_reported(session, client, monkeypatch):
    monkeypatch.setattr(config, "ENCRYPTION_KEY", "too-short")
    session.expire_all()

    with pytest.raises(ConfigurationError, match="not a valid key"):
        ClientRepository(session).get(client.id).full_name


def test_data_encrypted_with_another_key_is_reported(session, client, monkeypatch):
    """Changing the key makes the existing data unreadable, and says so."""
    monkeypatch.setattr(config, "ENCRYPTION_KEY", OTHER_KEY)
    session.expire_all()

    with pytest.raises(ConfigurationError, match="cannot be decrypted"):
        ClientRepository(session).get(client.id).full_name


def test_a_command_reports_a_missing_key_without_a_traceback(
    cli_database, sales_user, monkeypatch
):
    """Searching by email encrypts the email first: a missing key is a message."""
    email = sales_user.email
    monkeypatch.setattr(config, "ENCRYPTION_KEY", None)

    result = CliRunner().invoke(cli, ["login", "--email", email], input=f"{PASSWORD}\n")

    assert result.exit_code == 1
    assert "ENCRYPTION_KEY is missing" in result.stderr
    assert "Traceback" not in result.output + result.stderr

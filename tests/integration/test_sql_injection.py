"""Test that SQL injection payloads are treated as plain text."""

import pytest
from sqlalchemy import inspect

from epicevents.exceptions import InvalidCredentialsError
from epicevents.repositories import ClientRepository
from epicevents.services import auth
from epicevents.services import client as client_service

INJECTION = "Robert'); DROP TABLE clients;--"


@pytest.mark.parametrize("email", ["' OR '1'='1", "x@x.fr' OR 1=1 --"])
def test_sql_injection_in_email_does_not_bypass_authentication(
    session, sales_user, email
):
    """Reject login attempts containing SQL injection payloads."""
    with pytest.raises(InvalidCredentialsError):
        auth.authenticate(session, email, "anything")


def test_sql_injection_in_client_name_is_stored_as_text(session, sales_user):
    """Store SQL injection payloads as literal client names."""
    created = client_service.create_client(
        session,
        sales_user,
        full_name=INJECTION,
        email="robert@test.com",
        phone="+33 6 12 34 56 78",
        company_name="Test Company",
    )

    assert ClientRepository(session).get(created.id).full_name == INJECTION
    assert "clients" in inspect(session.get_bind()).get_table_names()

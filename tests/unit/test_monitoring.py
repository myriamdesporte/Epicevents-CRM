"""

Tests for Sentry reporting.
Sentry is mocked in all tests, so nothing is sent over the network.
"""

import pytest

from epicevents import monitoring

# Syntactically valid DSN that points nowhere.
FAKE_DSN = "https://abc123@o0.ingest.sentry.io/0"


class FakeUser:
    def __init__(self, employee_number):
        self.employee_number = employee_number
        self.full_name = "Bill Boquet"
        self.email = "bill@epicevents.fr"
        self.role = type("FakeRole", (), {"name": "sales"})()


class FakeContract:
    id = 12
    client_id = 3


@pytest.fixture
def options(monkeypatch):
    """Record the options passed to Sentry."""
    recorded = {}
    monkeypatch.setattr(
        monitoring.sentry_sdk, "init", lambda **kwargs: recorded.update(kwargs)
    )
    return recorded


@pytest.fixture
def messages(monkeypatch):
    """Record messages sent to Sentry."""
    sent = []
    monkeypatch.setattr(
        monitoring.sentry_sdk,
        "capture_message",
        lambda text, **kwargs: sent.append(text),
    )
    return sent


def test_nothing_starts_without_a_dsn(monkeypatch, options):
    """Sentry is not initialized when no DSN provided."""
    monkeypatch.setattr(monitoring, "SENTRY_DSN", None)

    monitoring.setup()

    assert options == {}


def test_local_variables_are_never_sent(monkeypatch, options):
    """Sentry must not collect local variables or personal data."""
    monkeypatch.setattr(monitoring, "SENTRY_DSN", FAKE_DSN)

    monitoring.setup()

    assert options["include_local_variables"] is False
    assert options["send_default_pii"] is False


def test_a_collaborator_change_is_reported(messages):
    """A collaborator change must be reported with both employee numbers."""
    monitoring.log_user_change("created", FakeUser("EE-100"), FakeUser("EE-001"))

    assert "created" in messages[0]
    assert "EE-100" in messages[0]
    assert "EE-001" in messages[0]


def test_a_reported_change_carries_no_personal_data(messages):
    """Names and email adresses must not be sent to Sentry."""
    monitoring.log_user_change("updated", FakeUser("EE-100"), FakeUser("EE-001"))

    assert "bill@epicevents.fr" not in messages[0]
    assert "Bill Boquet" not in messages[0]


def test_a_signature_is_reported(messages):
    """A contract signature must be reported with the contract and user IDs."""
    monitoring.log_contract_signed(FakeContract(), FakeUser("EE-003"))

    assert "signed" in messages[0]
    assert "12" in messages[0]
    assert "EE-003" in messages[0]

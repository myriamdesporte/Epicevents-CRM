"""Tests for the login, logout and whoami commands."""

import pytest
from click.testing import CliRunner
from sqlalchemy.exc import OperationalError

from epicevents.controllers.main import cli
from epicevents.services import auth
from epicevents.services.auth import load_token
from tests.conftest import PASSWORD


@pytest.fixture
def runner():
    return CliRunner()


def test_login_opens_a_session(runner, cli_database, sales_user):
    """The right email and password log the collaborator in."""
    result = runner.invoke(
        cli, ["login", "--email", sales_user.email], input=f"{PASSWORD}\n"
    )

    assert result.exit_code == 0
    assert "Logged in as" in result.output
    assert load_token() is not None


def test_login_reports_a_wrong_password_without_a_traceback(
    runner, cli_database, sales_user
):
    """A failed login must read as a message, not as a Python crash."""
    result = runner.invoke(
        cli, ["login", "--email", sales_user.email], input="wrong-password\n"
    )

    assert result.exit_code == 1
    assert "Traceback" not in result.output + result.stderr
    assert "wrong password" in result.stderr


def test_failed_login_stores_no_session(runner, cli_database, sales_user):
    """A failed login leaves no token behind."""
    runner.invoke(cli, ["login", "--email", sales_user.email], input="wrong\n")

    assert load_token() is None


def test_login_never_echoes_the_password(runner, cli_database, sales_user):
    """The password never appears in command prints."""
    result = runner.invoke(
        cli, ["login", "--email", sales_user.email], input=f"{PASSWORD}\n"
    )

    assert PASSWORD not in result.output


def test_password_is_not_a_command_line_option(runner):
    """There is no --password option, only --email."""
    result = runner.invoke(cli, ["login", "--help"])

    assert "--email" in result.output
    assert "--password" not in result.output


def test_whoami_shows_the_collaborator_and_their_role(runner, cli_database, sales_user):
    """whoami displays the logged-in collaborator's details."""
    runner.invoke(cli, ["login", "--email", sales_user.email], input=f"{PASSWORD}\n")
    result = runner.invoke(cli, ["whoami"])

    assert result.exit_code == 0
    assert sales_user.employee_number in result.output
    assert "sales" in result.output


def test_whoami_without_a_session_is_refused(runner, cli_database):
    """whoami refuses to run if nobody is logged in."""
    result = runner.invoke(cli, ["whoami"])

    assert result.exit_code == 1
    assert "Not logged in" in result.stderr


def test_logout_forgets_the_session(runner, cli_database, sales_user):
    """Logging out removes the stored session."""
    runner.invoke(cli, ["login", "--email", sales_user.email], input=f"{PASSWORD}\n")
    result = runner.invoke(cli, ["logout"])

    assert result.exit_code == 0
    assert load_token() is None


def test_logout_without_a_session_does_not_fail(runner, cli_database):
    """Logging out with no session to forget is not an error."""
    result = runner.invoke(cli, ["logout"])

    assert result.exit_code == 0


def test_unreachable_database_is_explained(runner, cli_database, monkeypatch):
    """An unreachable database gives a clear message, not a crash."""

    def refuse_connection(*_args, **_kwargs):
        raise OperationalError("SELECT 1", None, Exception("connection refused"))

    monkeypatch.setattr(auth, "login", refuse_connection)

    result = runner.invoke(
        cli, ["login", "--email", "bill@epicevents.fr"], input=f"{PASSWORD}\n"
    )

    assert result.exit_code == 1
    assert "Traceback" not in result.output + result.stderr
    assert "docker compose up" in result.stderr

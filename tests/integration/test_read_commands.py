"""Tests for the read commands: client list, contract list, event list."""

from decimal import Decimal

import pytest
from click.testing import CliRunner

from epicevents.controllers.main import cli
from tests.conftest import (
    PASSWORD,
    create_client,
    create_contract,
    create_event,
)


@pytest.fixture
def runner():
    """A runner with a wide terminal."""
    return CliRunner(env={"COLUMNS": "200"})


@pytest.fixture
def logged_in(runner, cli_database):
    """Log a collaborator in and return them."""

    def log_in(user):
        runner.invoke(cli, ["login", "--email", user.email], input=f"{PASSWORD}\n")
        return user

    return log_in


# --------------------------------------------------------------------------
# Authentication is required to read anything
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [["client", "list"], ["contract", "list"], ["event", "list"]],
)
def test_reading_requires_a_session(runner, cli_database, command):
    """No access to any data without being authenticated."""
    result = runner.invoke(cli, command)

    assert result.exit_code == 1
    assert "Not logged in" in result.stderr


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------


def test_every_collaborator_reads_every_client(
    session, logged_in, runner, sales_user, support_user
):
    """Read access is granted to all, whatever the department."""
    create_client(session, sales_user, full_name="Kevin Casey")
    logged_in(support_user)

    result = runner.invoke(cli, ["client", "list"])

    assert result.exit_code == 0
    assert "Kevin Casey" in result.output


def test_client_list_shows_the_sales_contact(
    session, logged_in, runner, sales_user, management_user
):
    """The client list displays the sales contact's name."""
    create_client(session, management_user, full_name="Lou Bouzin")
    logged_in(sales_user)

    result = runner.invoke(cli, ["client", "list"])

    assert management_user.full_name in result.output


def test_client_list_mine_keeps_only_my_clients(
    session, logged_in, runner, sales_user, management_user
):
    """--mine keeps only the clients of the logged-in collaborator."""
    create_client(session, sales_user, full_name="Kevin Casey")
    create_client(session, management_user, full_name="Lou Bouzin")
    logged_in(sales_user)

    result = runner.invoke(cli, ["client", "list", "--mine"])

    assert "Kevin Casey" in result.output
    assert "Lou Bouzin" not in result.output


def test_client_list_when_empty(session, logged_in, runner, sales_user):
    """An empty client list shows a message instead of an empty table."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["client", "list"])

    assert result.exit_code == 0
    assert "No client to display" in result.output


# --------------------------------------------------------------------------
# Contracts
# --------------------------------------------------------------------------


def test_contract_list_unsigned_only(session, logged_in, runner, sales_user, client):
    """--unsigned keeps only the contracts not yet signed."""
    create_contract(session, client, signed=True)
    create_contract(session, client, signed=False, total=Decimal("777.00"))
    logged_in(sales_user)

    result = runner.invoke(cli, ["contract", "list", "--unsigned"])

    assert "777.00" in result.output
    assert result.output.count("no") >= 1


def test_contract_list_unpaid_only(session, logged_in, runner, sales_user, client):
    """--unpaid keeps only the contracts still owing money."""
    create_contract(session, client, due=Decimal("0.00"), total=Decimal("111.00"))
    create_contract(session, client, due=Decimal("250.00"), total=Decimal("999.00"))
    logged_in(sales_user)

    result = runner.invoke(cli, ["contract", "list", "--unpaid"])

    assert "999.00" in result.output
    assert "111.00" not in result.output


def test_contract_list_mine_filters_by_client_sales_contact(
    session, logged_in, runner, sales_user, management_user
):
    """--mine includes only contracts belonging to clients assigned to the current user."""
    my_client = create_client(session, sales_user, full_name="Kevin Casey")
    other_client = create_client(session, management_user, full_name="Lou Bouzin")

    create_contract(session, my_client, total=Decimal("111.00"))
    create_contract(session, other_client, total=Decimal("222.00"))

    logged_in(sales_user)

    result = runner.invoke(cli, ["contract", "list", "--mine"])

    assert result.exit_code == 0
    assert "111.00" in result.output
    assert "222.00" not in result.output


def test_contract_list_with_unsigned_and_unpaid_filters(
    session, logged_in, runner, sales_user, client
):
    """Both filters must match for a contract to be included."""
    create_contract(
        session, client, signed=True, due=Decimal("100.00"), total=Decimal("111.00")
    )
    create_contract(
        session, client, signed=False, due=Decimal("0.00"), total=Decimal("222.00")
    )
    create_contract(
        session, client, signed=False, due=Decimal("50.00"), total=Decimal("333.00")
    )
    logged_in(sales_user)

    result = runner.invoke(cli, ["contract", "list", "--unsigned", "--unpaid"])

    assert "333.00" in result.output
    assert "111.00" not in result.output
    assert "222.00" not in result.output


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------


def test_event_list_without_support_only(
    session, logged_in, runner, sales_user, support_user, client
):
    """--no-support includes events without a support user, but excludes assigned events."""
    assigned_contract = create_contract(session, client)
    create_event(session, assigned_contract, support_user, name="Assigned")
    create_event(session, create_contract(session, client), None, name="Orphan")
    logged_in(sales_user)

    result = runner.invoke(cli, ["event", "list", "--no-support"])

    assert "Orphan" in result.output
    assert "Assigned" not in result.output


def test_event_list_mine_keeps_only_my_events(
    session, logged_in, runner, support_user, client
):
    """--mine keeps only the events assigned to the logged-in collaborator."""
    create_event(session, create_contract(session, client), support_user, name="Mine")
    create_event(session, create_contract(session, client), None, name="Orphan")
    logged_in(support_user)

    result = runner.invoke(cli, ["event", "list", "--mine"])

    assert "Mine" in result.output
    assert "Orphan" not in result.output


def test_event_without_support_shows_no_collaborator(
    session, logged_in, runner, sales_user, support_user, client
):
    """Events without a support contact are listed without displaying a collaborator."""
    create_event(session, create_contract(session, client), None, name="Orphan")
    logged_in(sales_user)

    result = runner.invoke(cli, ["event", "list"])

    assert result.exit_code == 0
    assert "Orphan" in result.output
    assert support_user.full_name not in result.output

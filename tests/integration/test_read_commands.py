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


@pytest.mark.parametrize(
    "command, message",
    [
        (["client", "list"], "No client to display"),
        (["contract", "list"], "No contract to display"),
        (["event", "list"], "No event to display"),
    ],
)
def test_an_empty_list_says_so(
    session, logged_in, runner, management_user, command, message
):
    """Empty lists display an appropriate message."""
    logged_in(management_user)

    result = runner.invoke(cli, command)

    assert result.exit_code == 0
    assert message in result.output


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


# --------------------------------------------------------------------------
# Detail views
# --------------------------------------------------------------------------


def test_client_show_displays_the_two_dates(
    session, logged_in, runner, sales_user, client
):
    """Client details display both dates."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["client", "show", str(client.id)])

    assert result.exit_code == 0
    assert "First contact" in result.output
    assert "Last update" in result.output


def test_event_show_displays_the_location_and_the_notes(
    session, logged_in, runner, sales_user, signed_contract
):
    """Event details display the location and notes."""
    event = create_event(session, signed_contract, None)
    event.notes = "Wedding starts at 3PM, by the river."
    session.commit()
    logged_in(sales_user)

    result = runner.invoke(cli, ["event", "show", str(event.id)])

    assert result.exit_code == 0
    assert "Chateau" in result.output
    assert "by the river" in result.output


def test_event_show_says_when_no_support_is_assigned(
    session, logged_in, runner, sales_user, signed_contract
):
    """Event details show when no support is assigned."""
    event = create_event(session, signed_contract, None)
    logged_in(sales_user)

    result = runner.invoke(cli, ["event", "show", str(event.id)])

    assert "nobody yet" in result.output


def test_contract_show_displays_the_amounts(
    session, logged_in, runner, sales_user, signed_contract
):
    """Contract details display the amounts."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["contract", "show", str(signed_contract.id)])

    assert result.exit_code == 0
    assert "1000.00" in result.output


def test_show_needs_a_session(runner, cli_database, client):
    """Show commands require authentication."""
    result = runner.invoke(cli, ["client", "show", str(client.id)])

    assert result.exit_code == 1
    assert "Not logged in" in result.stderr


def test_show_explains_an_unknown_id(session, logged_in, runner, sales_user):
    """An unknown client ID is explained."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["client", "show", "999"])

    assert result.exit_code == 1
    assert "No client has the id 999" in result.stderr

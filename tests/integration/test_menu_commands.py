"""Tests for the interactive menu."""

import pytest
from click.testing import CliRunner

from epicevents.controllers.main import cli
from tests.conftest import PASSWORD, create_client


@pytest.fixture
def runner():
    return CliRunner(env={"COLUMNS": "200"})


@pytest.fixture
def logged_in(runner, cli_database):
    """Log a collaborator in and return them."""

    def log_in(user):
        runner.invoke(cli, ["login", "--email", user.email], input=f"{PASSWORD}\n")
        return user

    return log_in


def test_the_menu_greets_the_signed_in_collaborator(
    session, logged_in, runner, sales_user
):
    """Test that the menu greets the logged-in collaborator."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["menu"], input="0\n")

    assert result.exit_code == 0
    assert sales_user.full_name in result.output
    assert "Clients" in result.output


def test_the_menu_asks_to_log_in_when_no_session(runner, cli_database, sales_user):
    """Test that the menu prompts for login when no session exists."""
    result = runner.invoke(cli, ["menu"], input=f"{sales_user.email}\n{PASSWORD}\n0\n")

    assert result.exit_code == 0
    assert "logging in" in result.output
    assert sales_user.full_name in result.output


def test_choosing_an_entity_shows_its_actions(session, logged_in, runner, sales_user):
    """Test that selecting an entity displays its available actions."""
    logged_in(sales_user)

    # 1 = Clients, then 0 = back, then 0 = leave.
    result = runner.invoke(cli, ["menu"], input="1\n0\n0\n")

    assert "List every client" in result.output
    assert "Create a client" in result.output


def test_an_action_runs_the_matching_command(
    session, logged_in, runner, sales_user, client
):
    """Test that selecting an action runs the corresponding command."""
    logged_in(sales_user)

    # Clients > List every client > back > leave
    result = runner.invoke(cli, ["menu"], input="1\n1\n0\n0\n")

    assert client.full_name in result.output


def test_an_action_needing_an_id_asks_for_it(
    session, logged_in, runner, sales_user, client
):
    """Test that an action requiring an ID prompts for it."""
    logged_in(sales_user)

    # Clients > Show one client > id > back > leave
    result = runner.invoke(cli, ["menu"], input=f"1\n3\n{client.id}\n0\n0\n")

    assert "First contact" in result.output


def test_a_refused_action_keeps_the_menu_alive(
    session, logged_in, runner, sales_user, management_user
):
    """The whole point of the menu: a refusal must not close the application."""
    other = create_client(session, management_user, full_name="Lou Bouzin")
    logged_in(sales_user)

    # Clients > Update a client > the colleague's id > a phone > back > leave
    result = runner.invoke(
        cli,
        ["menu"],
        input=f"1\n5\n{other.id}\n\n\n+33 6 00 00 00 00\n\n0\n0\n",
    )

    assert result.exit_code == 0
    assert "only update your own clients" in result.output + result.stderr
    # The menu was displayed again afterwards.
    assert result.output.count("List every client") >= 2


def test_the_menu_hides_what_the_collaborator_may_not_do(
    session, logged_in, runner, sales_user
):
    """Test that unauthorized actions are hidden from sales collaborators."""
    logged_in(sales_user)

    # Collaborators > back > leave
    result = runner.invoke(cli, ["menu"], input="4\n0\n0\n")

    assert "List every collaborator" in result.output
    assert "Create a collaborator" not in result.output
    assert "Delete a collaborator" not in result.output


def test_the_menu_offers_to_management_what_it_hides_from_sales(
    session, logged_in, runner, management_user
):
    """Test that management can access restricted actions."""
    logged_in(management_user)

    result = runner.invoke(cli, ["menu"], input="4\n0\n0\n")

    assert "Create a collaborator" in result.output
    assert "Delete a collaborator" in result.output


def test_an_out_of_range_choice_is_refused(session, logged_in, runner, sales_user):
    """Test that an invalid menu choice is rejected."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["menu"], input="99\n0\n")

    assert "Choose a number between" in result.output + result.stderr


def test_logging_out_from_the_menu(session, logged_in, runner, sales_user):
    """Test that selecting the logout option ends the session."""
    logged_in(sales_user)
    entities = 4  # Clients, Contracts, Events, Collaborators

    result = runner.invoke(cli, ["menu"], input=f"{entities + 1}\n")

    assert result.exit_code == 0
    assert "Logged out" in result.output

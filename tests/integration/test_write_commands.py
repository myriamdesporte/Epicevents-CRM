"""Tests for the write commands."""

import pytest
from click.testing import CliRunner

from epicevents.controllers.main import cli
from epicevents.repositories import ClientRepository, UserRepository
from tests.conftest import PASSWORD, create_client, create_contract, create_event


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


# --------------------------------------------------------------------------
# Collaborators
# --------------------------------------------------------------------------


def test_management_creates_a_collaborator(session, logged_in, runner, management_user):
    """Management can create a collaborator."""
    logged_in(management_user)

    result = runner.invoke(
        cli,
        [
            "user",
            "create",
            "--employee-number",
            "EE-100",
            "--full-name",
            "Nouvelle Recrue",
            "--email",
            "recrue@epicevents.fr",
            "--role",
            "support",
        ],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )

    assert result.exit_code == 0
    assert UserRepository(session).get_by_email("recrue@epicevents.fr") is not None


def test_the_password_is_never_echoed(session, logged_in, runner, management_user):
    """The password is never displayed."""
    logged_in(management_user)

    result = runner.invoke(
        cli,
        [
            "user",
            "create",
            "--employee-number",
            "EE-100",
            "--full-name",
            "Nouvelle Recrue",
            "--email",
            "recrue@epicevents.fr",
            "--role",
            "support",
        ],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )

    assert PASSWORD not in result.output


def test_a_password_cannot_be_passed_as_an_option(runner):
    """Password cannot be passed as an option."""
    result = runner.invoke(cli, ["user", "create", "--help"])

    assert "--password" not in result.output


def test_sales_is_refused_without_a_traceback(session, logged_in, runner, sales_user):
    """Sales cannot create a collaborator."""
    logged_in(sales_user)

    result = runner.invoke(
        cli,
        [
            "user",
            "create",
            "--employee-number",
            "EE-100",
            "--full-name",
            "Nouvelle Recrue",
            "--email",
            "recrue@epicevents.fr",
            "--role",
            "support",
        ],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )

    assert result.exit_code == 1
    assert "Traceback" not in result.output + result.stderr
    assert "does not allow" in result.stderr


def test_sales_is_refused_before_being_asked_anything(
    session, logged_in, runner, sales_user
):
    """Refuses access before asking for input."""
    logged_in(sales_user)

    result = runner.invoke(cli, ["user", "create"], input="")

    assert result.exit_code == 1
    assert "does not allow" in result.stderr
    for question in ("Employee number", "Full name", "Email", "Role", "Password"):
        assert question not in result.output


def test_deleting_a_collaborator_who_has_clients_is_explained(
    session, logged_in, runner, management_user, sales_user, client
):
    """Deleting a collaborator with clients is refused."""
    logged_in(management_user)

    result = runner.invoke(cli, ["user", "delete", str(sales_user.id)], input="y\n")

    assert result.exit_code == 1
    assert "Reassign them" in result.stderr


def test_an_unknown_id_is_explained(session, logged_in, runner, management_user):
    """An unknown collaborator ID is explained."""
    logged_in(management_user)

    result = runner.invoke(cli, ["user", "delete", "999"])

    assert result.exit_code == 1
    assert "No collaborator has the id 999" in result.stderr


def test_an_update_without_any_option_is_refused(
    session, logged_in, runner, management_user, sales_user
):
    """An update without options is refused."""
    logged_in(management_user)

    result = runner.invoke(cli, ["user", "update", str(sales_user.id)])

    assert result.exit_code != 0
    assert "at least one option" in result.output + result.stderr


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------


def test_a_sales_collaborator_creates_a_client_assigned_to_them(
    session, logged_in, runner, sales_user
):
    """A sales collaborator is assigned to their new client."""
    logged_in(sales_user)

    result = runner.invoke(
        cli,
        [
            "client",
            "create",
            "--full-name",
            "Kevin Casey",
            "--email",
            "kevin@startup.io",
            "--phone",
            "+678 123 456 78",
            "--company-name",
            "Cool Startup LLC",
        ],
    )

    assert result.exit_code == 0
    created = ClientRepository(session).list_all()[0]
    assert created.sales_contact_id == sales_user.id


def test_a_sales_collaborator_updates_their_own_client(
    session, logged_in, runner, sales_user, client
):
    """A sales collaborator can update their own client."""
    logged_in(sales_user)

    result = runner.invoke(
        cli, ["client", "update", str(client.id), "--phone", "+33 6 12 34 56 78"]
    )

    assert result.exit_code == 0
    session.refresh(client)
    assert client.phone == "+33 6 12 34 56 78"


def test_updating_a_colleagues_client_is_refused(
    session, logged_in, runner, sales_user, management_user
):
    """A sales collaborator cannot update another's client."""
    other = create_client(session, management_user, full_name="Lou Bouzin")
    logged_in(sales_user)

    result = runner.invoke(
        cli, ["client", "update", str(other.id), "--phone", "+33 6 00 00 00 00"]
    )

    assert result.exit_code == 1
    assert "only update your own clients" in result.stderr
    assert "Traceback" not in result.output + result.stderr


def test_a_malformed_email_is_explained(session, logged_in, runner, sales_user, client):
    """An invalid email format is rejected."""
    logged_in(sales_user)

    result = runner.invoke(
        cli, ["client", "update", str(client.id), "--email", "kevin-at-startup"]
    )

    assert result.exit_code == 1
    assert "not a valid email" in result.stderr


# --------------------------------------------------------------------------
# Contracts
# --------------------------------------------------------------------------


def test_management_creates_and_signs_a_contract(
    session, logged_in, runner, management_user, client
):
    """Management can create and sign a contract."""
    logged_in(management_user)

    created = runner.invoke(
        cli,
        [
            "contract",
            "create",
            "--client-id",
            str(client.id),
            "--total-amount",
            "1000.00",
            "--amount-due",
            "1000.00",
        ],
    )
    assert created.exit_code == 0

    contract_id = ClientRepository(session).get(client.id).contracts[0].id
    signed = runner.invoke(cli, ["contract", "sign", str(contract_id)])

    assert signed.exit_code == 0
    assert "signed" in signed.output


def test_an_amount_due_above_the_total_is_explained(
    session, logged_in, runner, management_user, client
):
    """The amount due cannot exceed the total amount."""
    logged_in(management_user)

    result = runner.invoke(
        cli,
        [
            "contract",
            "create",
            "--client-id",
            str(client.id),
            "--total-amount",
            "1000.00",
            "--amount-due",
            "1500.00",
        ],
    )

    assert result.exit_code == 1
    assert "cannot exceed" in result.stderr


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------


def test_sales_creates_an_event_then_management_assigns_support(
    session, logged_in, runner, sales_user, management_user, support_user, client
):
    """Sales can create an event and management can assign support."""
    contract = create_contract(session, client, signed=True)
    logged_in(sales_user)

    created = runner.invoke(
        cli,
        [
            "event",
            "create",
            "--contract-id",
            str(contract.id),
            "--name",
            "John Ouick Wedding",
            "--start",
            "2026-06-04 13:00",
            "--end",
            "2026-06-05 02:00",
            "--location",
            "Cande-sur-Beuvron",
            "--attendees",
            "75",
        ],
    )
    assert created.exit_code == 0

    event_id = contract.event.id
    logged_in(management_user)
    assigned = runner.invoke(
        cli,
        ["event", "assign-support", str(event_id), "--user-id", str(support_user.id)],
    )

    assert assigned.exit_code == 0
    assert support_user.full_name in assigned.output


def test_an_event_needs_a_signed_contract(
    session, logged_in, runner, sales_user, client
):
    """An event requires a signed contract."""
    unsigned = create_contract(session, client, signed=False)
    logged_in(sales_user)

    result = runner.invoke(
        cli,
        [
            "event",
            "create",
            "--contract-id",
            str(unsigned.id),
            "--name",
            "Trop tot",
            "--start",
            "2026-06-04 13:00",
            "--end",
            "2026-06-05 02:00",
            "--location",
            "Nulle part",
            "--attendees",
            "75",
        ],
    )

    assert result.exit_code == 1
    assert "not signed yet" in result.stderr


def test_a_badly_formatted_date_is_explained(
    session, logged_in, runner, sales_user, signed_contract
):
    """An invalid date format is rejected."""
    logged_in(sales_user)

    result = runner.invoke(
        cli,
        [
            "event",
            "create",
            "--contract-id",
            str(signed_contract.id),
            "--name",
            "Mauvaise date",
            "--start",
            "04/06/2026",
            "--end",
            "2026-06-05 02:00",
            "--location",
            "Quelque part",
            "--attendees",
            "75",
        ],
    )

    assert result.exit_code == 1
    assert "must look like" in result.stderr


def test_support_updates_the_event_assigned_to_them(
    session, logged_in, runner, support_user, signed_contract
):
    """Support can update their assigned event."""
    event = create_event(session, signed_contract, support_user)
    logged_in(support_user)

    result = runner.invoke(
        cli, ["event", "update", str(event.id), "--attendees", "200"]
    )

    assert result.exit_code == 0
    session.refresh(event)
    assert event.attendees == 200


def test_support_cannot_update_an_event_of_someone_else(
    session, logged_in, runner, support_user, signed_contract
):
    """Support cannot update an unassigned event."""
    event = create_event(session, signed_contract, None)
    logged_in(support_user)

    result = runner.invoke(
        cli, ["event", "update", str(event.id), "--attendees", "200"]
    )

    assert result.exit_code == 1
    assert "events you are responsible for" in result.stderr


# --------------------------------------------------------------------------
# Additional commands
# --------------------------------------------------------------------------


def test_user_list_shows_the_collaborators(
    session, logged_in, runner, management_user, sales_user
):
    """The user list shows collaborators."""
    logged_in(management_user)

    result = runner.invoke(cli, ["user", "list"])

    assert result.exit_code == 0
    assert sales_user.employee_number in result.output


def test_a_collaborator_without_clients_is_deleted(
    session, logged_in, runner, management_user, support_user
):
    """A collaborator without clients can be deleted."""
    support_id = support_user.id
    logged_in(management_user)

    result = runner.invoke(cli, ["user", "delete", str(support_id)], input="y\n")

    assert result.exit_code == 0
    assert UserRepository(session).get(support_id) is None


def test_changing_a_password_asks_for_it(
    session, logged_in, runner, management_user, sales_user
):
    """Changing a password prompts for the new password."""
    logged_in(management_user)

    result = runner.invoke(
        cli,
        ["user", "update", str(sales_user.id), "--change-password"],
        input="UnAutreMotDePasse42!\nUnAutreMotDePasse42!\n",
    )

    assert result.exit_code == 0
    session.refresh(sales_user)
    assert sales_user.check_password("UnAutreMotDePasse42!") is True


def test_contract_amounts_can_be_updated(
    session, logged_in, runner, management_user, signed_contract
):
    """Management can update contract amounts."""
    logged_in(management_user)

    result = runner.invoke(
        cli, ["contract", "update", str(signed_contract.id), "--amount-due", "0.00"]
    )

    assert result.exit_code == 0
    session.refresh(signed_contract)
    assert signed_contract.amount_due == 0

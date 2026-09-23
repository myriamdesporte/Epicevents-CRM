"""An interactive menu, for collaborators who would rather not type commands."""

import click

from epicevents import database
from epicevents.controllers.errors import handle_errors
from epicevents.services import auth
from epicevents.views.console import (
    console,
    print_error,
    print_info,
    print_menu,
    print_title,
)

EDITABLE = {
    "client": [
        ("--full-name", "Full name"),
        ("--email", "Email"),
        ("--phone", "Phone"),
        ("--company-name", "Company name"),
    ],
    "contract": [
        ("--total-amount", "Total amount"),
        ("--amount-due", "Amount still due"),
    ],
    "event": [
        ("--name", "Name"),
        ("--start", "Start"),
        ("--end", "End"),
        ("--location", "Location"),
        ("--attendees", "Attendees"),
        ("--notes", "Notes"),
    ],
    "user": [
        ("--employee-number", "Employee number"),
        ("--full-name", "Full name"),
        ("--email", "Email"),
        ("--role", "Role"),
    ],
}


ACTIONS = {
    "Clients": [
        ("List every client", ["client", "list"]),
        ("List my clients", ["client", "list", "--mine"]),
        ("Show one client", ["client", "show", "<id>"]),
        ("Create a client", ["client", "create"]),
        ("Update a client", ["client", "update", "<id>"]),
    ],
    "Contracts": [
        ("List every contract", ["contract", "list"]),
        ("List the unsigned ones", ["contract", "list", "--unsigned"]),
        ("List those still owing money", ["contract", "list", "--unpaid"]),
        ("Show one contract", ["contract", "show", "<id>"]),
        ("Create a contract", ["contract", "create"]),
        ("Update a contract", ["contract", "update", "<id>"]),
        ("Sign a contract", ["contract", "sign", "<id>"]),
    ],
    "Events": [
        ("List every event", ["event", "list"]),
        ("List those without support", ["event", "list", "--no-support"]),
        ("List the events assigned to me", ["event", "list", "--mine"]),
        ("Show one event", ["event", "show", "<id>"]),
        ("Create an event", ["event", "create"]),
        ("Update an event", ["event", "update", "<id>"]),
        ("Assign a support collaborator", ["event", "assign-support", "<id>"]),
    ],
    "Collaborators": [
        ("List every collaborator", ["user", "list"]),
        ("Create a collaborator", ["user", "create"]),
        ("Update a collaborator", ["user", "update", "<id>"]),
        ("Delete a collaborator", ["user", "delete", "<id>"]),
    ],
}


def run(arguments) -> None:
    """Run one command, keeping the menu alive whatever happens."""

    from epicevents.controllers.main import cli

    try:
        cli.main(args=list(arguments), standalone_mode=False)
    except SystemExit:
        pass
    except click.ClickException as error:
        print_error(error.format_message())
    except click.Abort:
        print_info("Cancelled.")


def ask_choice(title: str, entries: list[str]) -> int | None:
    """Show numbered entries and return the chosen index, or None to go back."""
    print_menu(title, entries)

    choice = click.prompt("Your choice", type=int, default=0, show_default=False)

    if choice == 0:
        return None

    if not 1 <= choice <= len(entries):
        print_error(f"Choose a number between 0 and {len(entries)}.")
        return ask_choice(title, entries)

    return choice - 1


def with_identifier(arguments) -> list[str]:
    """Replace the "<id>" placeholder by a number asked for now."""
    if "<id>" not in arguments:
        return arguments

    identifier = click.prompt("Which id", type=int)
    return [str(identifier) if part == "<id>" else part for part in arguments]


def ask_updates(entity: str) -> list[str]:
    """Ask what to change, field by field, leaving blank to keep a value."""
    print_info("Leave blank to keep the current value.")

    given = []
    for option, label in EDITABLE[entity]:
        value = click.prompt(label, default="", show_default=False)
        if value:
            given += [option, value]

    return given


def entity_menu(name: str) -> None:
    """Offer the actions available on one entity, until the reader goes back."""
    actions = ACTIONS[name]
    labels = [label for label, _ in actions]

    while True:
        chosen = ask_choice(name, labels)
        if chosen is None:
            return

        arguments = with_identifier(actions[chosen][1])

        if arguments[1] == "update":
            changes = ask_updates(arguments[0])
            if not changes:
                print_info("Nothing changed.")
                continue
            arguments += changes

        run(arguments)


def current_collaborator():
    """Return the collaborator of the stored session, or None."""
    with database.Session() as session:
        try:
            user = auth.get_current_user(session)
            return f"{user.full_name} ({user.role.name})"
        except auth.AuthenticationError:
            return None


@click.command()
@handle_errors
def menu() -> None:
    """Browse the CRM through a menu instead of typing commands."""
    print_title("Epic Events CRM")

    if current_collaborator() is None:
        print_info("No session yet -- logging in.")
        run(["login"])

        if current_collaborator() is None:
            return

    entities = list(ACTIONS)

    while True:
        who = current_collaborator()
        if who is None:
            print_info("Session over.")
            return

        chosen = ask_choice(f"Signed in as {who}", entities + ["Log out"])

        if chosen is None:
            print_info("Goodbye.")
            return

        if chosen == len(entities):
            run(["logout"])
            return

        entity_menu(entities[chosen])

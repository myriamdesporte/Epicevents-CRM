"""Fill the database with a demonstration dataset."""

import argparse
import getpass
import sys

from sqlalchemy import select

from epicevents.database import Session
from epicevents.models import Client, Contract, Event, RoleName, User
from epicevents.services import client as client_service
from epicevents.services import contract as contract_service
from epicevents.services import event as event_service
from epicevents.services import user as user_service
from epicevents.services.auth import AuthorizationError
from epicevents.validators import ValidationError, validate_password

COLLABORATORS = [
    ("DEMO-01", "Bill Boquet", "bill@epicevents.com", RoleName.SALES),
    ("DEMO-02", "Anne Aunim", "anne@epicevents.com", RoleName.SALES),
    ("DEMO-03", "Kate Hastroff", "kate@epicevents.com", RoleName.SUPPORT),
    ("DEMO-04", "Alienor Vichum", "alienor@epicevents.com", RoleName.SUPPORT),
]

# Clients, and which sales collaborator follows each one.
CLIENTS = [
    (
        "bill@epicevents.com",
        "Kevin Casey",
        "kevin@startup.io",
        "+678 123 456 78",
        "Cool Startup LLC",
    ),
    (
        "bill@epicevents.com",
        "John Ouick",
        "john.ouick@gmail.com",
        "+1 234 567 8901",
        "Ouick Family",
    ),
    (
        "anne@epicevents.com",
        "Lou Bouzin",
        "jacky@loubouzin.grd",
        "+666 12345",
        "Lou Bouzin SARL",
    ),
]

# Contracts: client, total, still due, signed.
CONTRACTS = [
    ("John Ouick", "12000.00", "0.00", True),
    ("Lou Bouzin", "8000.00", "2500.00", True),
    ("Kevin Casey", "1200.00", "600.00", True),
    ("Kevin Casey", "3500.00", "3500.00", False),
]

# Events, on the signed contracts.
EVENTS = [
    {
        "client": "John Ouick",
        "name": "John Ouick Wedding",
        "start_date": "2026-06-04 13:00",
        "end_date": "2026-06-05 02:00",
        "location": "53 Rue du Chateau, 41120 Cande-sur-Beuvron, France",
        "attendees": "75",
        "notes": (
            "Wedding starts at 3PM, by the river. Catering is organized, "
            "reception starts at 5PM."
        ),
        "support": "kate@epicevents.com",
    },
    {
        "client": "Lou Bouzin",
        "name": "Lou Bouzin General Assembly",
        "start_date": "2026-05-05 15:00",
        "end_date": "2026-05-05 17:00",
        "location": "Salle des fetes de Mufflins",
        "attendees": "200",
        "notes": "Assemblee generale des actionnaires (~200 personnes).",
        "support": None,
    },
]


def management_user(session):
    """Return the management collaborator."""
    user = session.scalars(
        select(User).join(User.role).where(User.role.has(name=RoleName.MANAGEMENT))
    ).first()

    if user is None:
        sys.exit(
            "No management collaborator found: run 'python create_first_user.py' "
            "first."
        )

    return user


def ask_password() -> str:
    """Ask once for the password shared by every demonstration account."""
    while True:
        try:
            password = validate_password(
                getpass.getpass("Password for the demo accounts: ")
            )
        except ValidationError as error:
            print(error)
            continue

        if password != getpass.getpass("Confirm password: "):
            print("Passwords do not match.")
            continue

        return password


def already_filled(session) -> bool:
    """Return whether any client exists."""
    return session.scalar(select(Client.id).limit(1)) is not None


def wipe(session, keep: User) -> None:
    """Delete demonstration data while keeping the current collaborator."""
    for model in (Event, Contract, Client):
        for row in session.scalars(select(model)):
            session.delete(row)
    session.flush()

    for user in session.scalars(select(User).where(User.id != keep.id)):
        session.delete(user)

    session.commit()
    print("Previous data deleted.")


def seed(session, manager: User, password: str) -> None:
    """Create the whole dataset, through the services."""
    people = {manager.email: manager}

    for employee_number, full_name, email, role in COLLABORATORS:
        people[email] = user_service.create_user(
            session,
            manager,
            employee_number=employee_number,
            full_name=full_name,
            email=email,
            password=password,
            role_name=role,
        )
    print(f"{len(COLLABORATORS)} collaborators created.")

    clients = {}
    for sales_email, full_name, email, phone, company in CLIENTS:
        clients[full_name] = client_service.create_client(
            session,
            people[sales_email],
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company,
        )
    print(f"{len(CLIENTS)} clients created.")

    signed = {}
    for client_name, total, due, is_signed in CONTRACTS:
        contract = contract_service.create_contract(
            session,
            manager,
            client_id=clients[client_name].id,
            total_amount=total,
            amount_due=due,
            is_signed=is_signed,
        )
        # Keep one signed contract per client for events.
        if is_signed:
            signed.setdefault(client_name, contract)
    print(f"{len(CONTRACTS)} contracts created.")

    for description in EVENTS:
        client = clients[description["client"]]
        event = event_service.create_event(
            session,
            client.sales_contact,
            contract_id=signed[description["client"]].id,
            name=description["name"],
            start_date=description["start_date"],
            end_date=description["end_date"],
            location=description["location"],
            attendees=description["attendees"],
            notes=description["notes"],
        )

        if description["support"] is not None:
            event_service.assign_support(
                session, manager, event, people[description["support"]]
            )
    print(f"{len(EVENTS)} events created.")


def report(manager: User) -> None:
    """Display the accounts created for the demonstration."""
    print("\nAccounts, all sharing the password you just typed:")
    print(f"  {manager.email:<28} management (yours, password unchanged)")
    for _, full_name, email, role in COLLABORATORS:
        print(f"  {email:<28} {role} -- {full_name}")

    print("\nStart with:")
    print("  python -m epicevents login")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete every client, contract, event and collaborator first",
    )
    arguments = parser.parse_args()

    with Session() as session:
        manager = management_user(session)

        if already_filled(session):
            if not arguments.reset:
                sys.exit(
                    "The database already holds clients: run with --reset to "
                    "replace them, or use an empty database."
                )
            wipe(session, keep=manager)

        try:
            seed(session, manager, ask_password())
        except (ValidationError, AuthorizationError) as error:
            sys.exit(f"Refused by the application: {error}")

        report(manager)


if __name__ == "__main__":
    main()

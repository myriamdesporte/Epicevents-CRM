"""Display of the collaborators and of the session."""

from epicevents.views.console import (
    print_details,
    print_info,
    print_success,
    print_table,
)

COLUMNS = ("ID", "Employee number", "Name", "Email", "Role")


def as_row(user) -> tuple[str, ...]:
    """Turn a collaborator into the cells of a table row."""
    return (
        str(user.id),
        user.employee_number,
        user.full_name,
        user.email,
        user.role.name,
    )


def show_list(users) -> None:
    """Display a list of collaborators, or say there is none."""
    if not users:
        print_info("No collaborator to display.")
        return

    print_table("Collaborators", COLUMNS, [as_row(user) for user in users])


def show_saved(user) -> None:
    """Confirm that a collaborator was created or updated."""
    print_success(f"Collaborator saved: {user.full_name} ({user.role.name}).")


def show_deleted(user) -> None:
    """Confirm that a collaborator was deleted."""
    print_success(f"Collaborator deleted: {user.full_name}.")


def show_login(user) -> None:
    """Confirm that a session has been opened."""
    print_success(f"Logged in as {user.full_name} ({user.role.name}).")


def show_logout() -> None:
    """Confirm that the stored session has been forgotten."""
    print_success("Logged out.")


def show_current_user(user) -> None:
    """Display who the current session belongs to."""
    print_details(
        "Current session",
        {
            "Employee number": user.employee_number,
            "Name": user.full_name,
            "Email": user.email,
            "Role": user.role.name,
        },
    )

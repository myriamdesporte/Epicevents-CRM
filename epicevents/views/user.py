"""Display of the collaborators and of the session."""

from epicevents.views.console import print_details, print_success


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

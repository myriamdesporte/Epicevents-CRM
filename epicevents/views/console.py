"""Display building blocks, built on rich.

The only file in the project that imports rich. The other views describe
what to show for one entity; this module knows how to put it on screen.
Changing the whole look of the application therefore touches a single file.
"""

from rich import box
from rich.console import Console
from rich.table import Table

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

console = Console()
error_console = Console(stderr=True)


def format_datetime(value) -> str:
    """Write a date and time in the reader's local time."""
    if value.tzinfo is not None:
        value = value.astimezone()

    return value.strftime(DATETIME_FORMAT)


def print_success(message: str) -> None:
    """Report an action that went through."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Report a failure, on the error stream."""
    error_console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Report something neutral, such as an empty result."""
    console.print(message)


def print_table(title: str, columns: tuple[str, ...], rows: list[tuple]) -> None:
    """Display rows under the given column headers."""
    table = Table(title=title, box=box.SIMPLE_HEAD)

    for column in columns:
        table.add_column(column)

    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_details(title: str, rows: dict[str, str]) -> None:
    """Display a set of field and value pairs as a table."""
    table = Table(title=title, show_header=False, box=box.SIMPLE)
    table.add_column(style="bold")
    table.add_column()

    for field, value in rows.items():
        table.add_row(field, value)

    console.print(table)

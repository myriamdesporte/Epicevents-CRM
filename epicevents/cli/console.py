"""Terminal output helpers, built on rich."""

from rich import box
from rich.console import Console
from rich.table import Table

console = Console()
error_console = Console(stderr=True)


def print_success(message: str) -> None:
    """Report an action that went through."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Report a failure, on the error stream."""
    error_console.print(f"[red]✗[/red] {message}")


def print_details(title: str, rows: dict[str, str]) -> None:
    """Display a set of field and value pairs as a table."""
    table = Table(title=title, show_header=False, box=box.SQUARE)
    table.add_column(style="bold")
    table.add_column()

    for field, value in rows.items():
        table.add_row(field, value)

    console.print(table)

"""Display building blocks, built on rich.

The only file in the project that imports rich.
"""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

console = Console()
error_console = Console(stderr=True)


def format_datetime(value) -> str:
    """Write a date and time in the reader's local time.

    The exact reverse of what the validators do on input: the collaborator types
    a local time, the database stores UTC, and the display converts it back.
    A value read without a timezone is written as it is.
    """
    if value.tzinfo is not None:
        value = value.astimezone()

    return value.strftime(DATETIME_FORMAT)


def format_money(amount) -> str:
    """Write an amount with two decimals and a separator every three digits.

    "12,000.00" rather than "12000.00": the eye counts groups, not digits.
    """
    return f"{amount:,.2f}"


def format_yes_no(value: bool) -> str:
    """Write a yes or no answer, in green or in red."""
    return "[green]yes[/green]" if value else "[red]no[/red]"


def format_attention(text: str) -> str:
    """Write a value someone still has to act on, in amber."""
    return f"[yellow]{text}[/yellow]"


def print_success(message: str) -> None:
    """Report an action that went through."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Report a failure, on the error stream."""
    error_console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Report something neutral, such as an empty result."""
    console.print(message)


def print_title(text: str) -> None:
    """Announce a section, with a blank line above it."""
    console.print(f"\n[bold]{text}[/bold]")


def print_menu(title: str, entries: list[str]) -> None:
    """Display numbered entries, plus a last line to go back."""
    print_title(title)

    for number, entry in enumerate(entries, start=1):
        console.print(f"  {number}. {entry}")

    console.print("  0. Back")


def print_table(
    title: str,
    columns: tuple[str, ...],
    rows: list[tuple],
    right: tuple[str, ...] = (),
) -> None:
    """Display rows under the given column headers."""
    table = Table(
        title=f"{title} ({len(rows)})",
        box=box.SIMPLE_HEAD,
        title_style="bold",
        header_style="bold cyan",
    )

    for column in columns:
        table.add_column(column, justify="right" if column in right else "left")

    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_details(title: str, rows: dict[str, str]) -> None:
    """Display one record as a framed card."""
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column(style="cyan")
    table.add_column()

    for field, value in rows.items():
        table.add_row(field, value)

    console.print(
        Panel(table, title=f"[bold]{title}[/bold]", box=box.ROUNDED, expand=False)
    )

"""Read the options a collaborator typed for an update command
or ask for the missing ones."""

import click


def ask(value, label: str, **prompt_options):
    """Return the provided value or prompt the user for one."""
    if value is not None:
        return value

    return click.prompt(label, **prompt_options)


def given(**options) -> dict:
    """Keep only the options the collaborator actually typed."""
    return {name: value for name, value in options.items() if value is not None}

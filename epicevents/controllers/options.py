"""Reading the options of an update command."""


def given(**options) -> dict:
    """Keep only the options the collaborator actually typed."""
    return {name: value for name, value in options.items() if value is not None}

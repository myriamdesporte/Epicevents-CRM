import sentry_sdk

from epicevents.config import SENTRY_DSN


def setup() -> None:
    """Start reporting, if a DSN is configured."""
    sentry_sdk.init()

    if not SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        include_local_variables=False,
        send_default_pii=False,
    )


def log_user_change(action: str, user, by) -> None:
    """Record that a collaborator was created, updated or deleted."""
    sentry_sdk.capture_message(
        f"Collaborator {action}: {user.employee_number} "
        f"(role {user.role.name}) by {by.employee_number}",
        level="info",
    )


def log_contract_signed(contract, by) -> None:
    """Record the signature of a contract."""
    sentry_sdk.capture_message(
        f"Contract {contract.id} signed for client {contract.client_id} "
        f"by {by.employee_number} ",
        level="info",
    )

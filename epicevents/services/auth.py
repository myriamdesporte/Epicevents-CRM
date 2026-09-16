"""Authentication and authorization for the Epic Events CRM."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from sqlalchemy.orm import Session as SessionType

from epicevents.config import JWT_SECRET
from epicevents.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    InvalidCredentialsError,
    AuthorizationError,
)
from epicevents.models import User
from epicevents.permissions import Permission, has_permission
from epicevents.repositories import UserRepository
from epicevents.security import hash_password, needs_rehash

TOKEN_LIFETIME = timedelta(hours=10)
ALGORITHM = "HS256"
TOKEN_PATH = Path.home() / ".epicevents" / "token"
MIN_SECRET_LENGTH = 32
INVALID_CREDENTIALS = "Unknown email address or wrong password."


def _secret() -> str:
    """Return the signing secret, refusing a missing or too short one."""
    if not JWT_SECRET:
        raise AuthenticationError(
            "JWT_SECRET is missing from the environment: copy .env.example to "
            ".env and set it."
        )
    if len(JWT_SECRET) < MIN_SECRET_LENGTH:
        raise AuthenticationError(
            f"JWT_SECRET is too short ({len(JWT_SECRET)} characters): at least "
            f"{MIN_SECRET_LENGTH} are required. Generate one with "
            'python -c "import secrets; print(secrets.token_urlsafe(64))"'
        )
    return JWT_SECRET


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------


def authenticate(session: SessionType, email: str, password: str) -> User:
    """Return the collaborator matching an email and password pair.
    Raises InvalidCredentialsError if either is wrong.
    """
    user = UserRepository(session).get_by_email(email)

    if user is None:
        hash_password(password)
        raise InvalidCredentialsError(INVALID_CREDENTIALS)

    if not user.check_password(password):
        raise InvalidCredentialsError(INVALID_CREDENTIALS)

    return user


def create_token(user: User) -> str:
    """Return a signed token identifying a collaborator for a limited time."""
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "iat": issued_at,
        "exp": issued_at + TOKEN_LIFETIME,
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def read_token(token: str) -> int:
    """Return the collaborator id carried by a valid token.
    Raises TokenExpiredError or InvalidTokenError otherwise.
    """
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise TokenExpiredError("Session expired, please log in again.") from error
    except jwt.InvalidTokenError as error:
        raise InvalidTokenError("Invalid session, please log in again.") from error

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidTokenError("Malformed session token.") from error


def store_token(token: str) -> None:
    """Write the token to the user's home directory, readable by them only."""
    TOKEN_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    TOKEN_PATH.touch(mode=0o600, exist_ok=True)
    TOKEN_PATH.chmod(0o600)
    TOKEN_PATH.write_text(token, encoding="utf-8")


def load_token() -> str | None:
    """Return the stored token, or None when no session is stored."""
    if not TOKEN_PATH.exists():
        return None
    return TOKEN_PATH.read_text(encoding="utf-8").strip() or None


def clear_token() -> None:
    """Forget the stored session. Logging out never fails."""
    TOKEN_PATH.unlink(missing_ok=True)


def login(session: SessionType, email: str, password: str) -> User:
    """Authenticate a collaborator and open a session on this machine."""
    user = authenticate(session, email, password)

    if needs_rehash(user.password_hash):
        user.set_password(password)
        session.commit()

    store_token(create_token(user))
    return user


def get_current_user(session: SessionType) -> User:
    """Return the collaborator identified by the stored session token."""
    token = load_token()
    if token is None:
        raise AuthenticationError("Not logged in: run the login command first.")

    user: User | None = UserRepository(session).get(read_token(token))
    if user is None:
        raise InvalidTokenError("This session refers to a deleted collaborator.")

    return user


# --------------------------------------------------------------------------
# Authorization
# --------------------------------------------------------------------------


def authorize(user: User, permission: Permission) -> None:
    """Raise AuthorizationError unless the collaborator's role allows the action."""
    if not has_permission(user.role.name, permission):
        raise AuthorizationError(
            f"Your role ({user.role.name}) does not allow this action: "
            f"{permission}."
        )

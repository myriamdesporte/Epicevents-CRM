"""Tests for authentication and authorization."""

from datetime import timedelta

import jwt
import pytest

from epicevents.services import auth
from epicevents.services.auth import (
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    authenticate,
    authorize,
    clear_token,
    create_token,
    get_current_user,
    load_token,
    login,
    read_token,
)
from epicevents.permissions import Permission
from tests.conftest import PASSWORD

# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------


def test_authenticate_returns_the_collaborator(session, sales_user):
    """The right email/password pair returns the matching collaborator."""
    assert authenticate(session, sales_user.email, PASSWORD) is sales_user


def test_authenticate_rejects_a_wrong_password(session, sales_user):
    """A known email with the wrong password is refused."""
    with pytest.raises(InvalidCredentialsError):
        authenticate(session, sales_user.email, "WrongPassword1!")


def test_authenticate_rejects_an_unknown_email(session, sales_user):
    """An email with no matching account is refused."""
    with pytest.raises(InvalidCredentialsError):
        authenticate(session, "nobody@epicevents.fr", PASSWORD)


def test_authenticate_does_not_reveal_which_part_is_wrong(session, sales_user):
    """Same message either way, so addresses cannot be enumerated."""
    with pytest.raises(InvalidCredentialsError) as wrong_password:
        authenticate(session, sales_user.email, "WrongPassword1!")

    with pytest.raises(InvalidCredentialsError) as unknown_email:
        authenticate(session, "nobody@epicevents.fr", PASSWORD)

    assert str(wrong_password.value) == str(unknown_email.value)


# --------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------


def test_token_carries_the_collaborator_id(session, sales_user):
    """A token, once decoded, identifies the collaborator it was issued for."""
    assert read_token(create_token(sales_user)) == sales_user.id


def test_expired_token_is_refused(session, sales_user, monkeypatch):
    """A token issued in the past must no longer open a session."""
    monkeypatch.setattr(auth, "TOKEN_LIFETIME", timedelta(seconds=-1))
    expired = create_token(sales_user)

    with pytest.raises(TokenExpiredError):
        read_token(expired)


def test_token_signed_with_another_secret_is_refused(session, sales_user):
    """A token signed with a different key is rejected."""
    token_signed_with_wrong_secret = jwt.encode(
        {"sub": str(sales_user.id)},
        "wrong-secret-key-but-valid-length",
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError):
        read_token(token_signed_with_wrong_secret)


def test_unsigned_token_is_refused(session, sales_user):
    """A token claiming 'no signature needed' (alg=none) is rejected."""
    unsigned_token = jwt.encode({"sub": str(sales_user.id)}, key="", algorithm="none")

    with pytest.raises(InvalidTokenError):
        read_token(unsigned_token)


def test_token_without_a_subject_is_refused(session):
    """A token missing the collaborator id cannot be used to identify anyone."""
    token_without_subject = jwt.encode(
        {"foo": "bar"}, auth.JWT_SECRET, algorithm=auth.ALGORITHM
    )

    with pytest.raises(InvalidTokenError):
        read_token(token_without_subject)


def test_altered_token_is_refused(session, sales_user):
    """Changing a single character breaks the signature."""
    token = create_token(sales_user)
    middle = len(token) // 2
    altered = (
        token[:middle] + ("A" if token[middle] != "A" else "B") + token[middle + 1:]
    )
    with pytest.raises(InvalidTokenError):
        read_token(altered)


def test_missing_secret_is_reported(session, sales_user, monkeypatch):
    """A missing JWT_SECRET gives a clear error."""
    monkeypatch.setattr(auth, "JWT_SECRET", None)

    with pytest.raises(AuthenticationError, match="JWT_SECRET is missing"):
        create_token(sales_user)


def test_too_short_secret_is_refused(session, sales_user, monkeypatch):
    """A secret shorter than the minimum length is rejected."""
    monkeypatch.setattr(auth, "JWT_SECRET", "short")

    with pytest.raises(AuthenticationError, match="too short"):
        create_token(sales_user)


# --------------------------------------------------------------------------
# Session persistence
# --------------------------------------------------------------------------


def test_login_stores_a_session(session, sales_user):
    """A successful login leaves a token on disk."""
    login(session, sales_user.email, PASSWORD)
    assert load_token() is not None


def test_login_does_not_store_anything_on_failure(session, sales_user):
    """A failed login attempt must not leave a usable session behind."""
    with pytest.raises(InvalidCredentialsError):
        login(session, sales_user.email, "WrongPassword1!")

    assert load_token() is None


def test_login_upgrades_an_outdated_hash(session, sales_user, monkeypatch):
    """Logging in replaces an outdated password hash."""
    monkeypatch.setattr(auth, "needs_rehash", lambda password_hash: True)
    outdated = sales_user.password_hash

    login(session, sales_user.email, PASSWORD)

    assert sales_user.password_hash != outdated
    assert sales_user.check_password(PASSWORD) is True


def test_session_of_a_deleted_collaborator_is_refused(session, sales_user):
    """A collaborator removed by management must lose access immediately, even
    though their token is still within its validity period."""
    login(session, sales_user.email, PASSWORD)

    session.delete(sales_user)
    session.commit()

    with pytest.raises(InvalidTokenError, match="deleted collaborator"):
        get_current_user(session)


def test_token_file_is_readable_by_its_owner_only(session, sales_user):
    """The token file is accessible only by its owner."""
    login(session, sales_user.email, PASSWORD)
    permissions = auth.TOKEN_PATH.stat().st_mode & 0o777

    assert permissions == 0o600


def test_current_user_is_found_from_the_stored_session(session, sales_user):
    """The stored token is enough to retrieve the logged-in collaborator."""
    login(session, sales_user.email, PASSWORD)
    assert get_current_user(session) is sales_user


def test_current_user_requires_a_session(session):
    """No stored token means no way to identify a current collaborator."""
    with pytest.raises(AuthenticationError, match="Not logged in"):
        get_current_user(session)


def test_logout_forgets_the_session(session, sales_user):
    """Logging out removes the token, ending the session."""
    login(session, sales_user.email, PASSWORD)
    clear_token()

    assert load_token() is None
    with pytest.raises(AuthenticationError):
        get_current_user(session)


# --------------------------------------------------------------------------
# Authorization
# --------------------------------------------------------------------------


def test_authorize_allows_a_permitted_action(session, management_user):
    """A role with the required permission is let through."""
    authorize(management_user, Permission.USER_CREATE)


def test_authorize_refuses_missing_permission(session, sales_user):
    """An action is rejected when the user lacks its permission."""
    with pytest.raises(AuthorizationError):
        authorize(sales_user, Permission.USER_CREATE)


def test_support_cannot_create_clients(session, support_user):
    """Client creation is out of scope for the support role."""
    with pytest.raises(AuthorizationError):
        authorize(support_user, Permission.CLIENT_CREATE)


def test_sales_can_create_clients(session, sales_user):
    """Client creation is within scope for the sales role."""
    authorize(sales_user, Permission.CLIENT_CREATE)

"""Tests for the password API exposed by the User model."""

from epicevents.models import User

PASSWORD = "DummyPassword42!"


def make_user() -> User:
    """Return a user with a set password."""
    user = User(
        employee_number="EE-001",
        full_name="Bill Boquet",
        email="bill.boquet@epicevents.fr",
        role_id=1,
    )
    user.set_password(PASSWORD)
    return user


def test_set_password_stores_a_hash():
    """set_password must never store the plaintext password."""
    user = make_user()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$argon2id$")


def test_check_password_accepts_the_right_password():
    """check_password must return True for the password that was set."""
    assert make_user().check_password(PASSWORD) is True


def test_check_password_rejects_a_wrong_password():
    """check_password must return False for any other password."""
    assert make_user().check_password("WrongPassword1!") is False


def test_repr_does_not_leak_the_password_hash():
    """__repr__ ends up in logs and tracebacks: it must stay harmless."""
    user = make_user()
    assert user.password_hash not in repr(user)
    assert PASSWORD not in repr(user)

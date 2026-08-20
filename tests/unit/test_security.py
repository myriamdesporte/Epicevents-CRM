"""Tests for password hashing."""

from epicevents.security import hash_password, verify_password

PASSWORD = "DummyPassword42!"


def test_hash_never_contains_the_password():
    """The stored value must not leak the password it was built from."""
    assert PASSWORD not in hash_password(PASSWORD)


def test_hash_uses_argon2id():
    """hash_password must produce an Argon2id hash."""
    assert hash_password(PASSWORD).startswith("$argon2id$")


def test_same_password_gets_different_hashes():
    """hash_password must salt each hash so identical passwords differ."""
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_verify_accepts_the_right_password():
    """verify_password must return True for the password that produced the hash."""
    assert verify_password(hash_password(PASSWORD), PASSWORD) is True


def test_verify_rejects_a_wrong_password():
    """verify_password must return False for any other password."""
    assert verify_password(hash_password(PASSWORD), "WrongPassword1!") is False


def test_verify_rejects_an_empty_password():
    """verify_password must reject an empty password like any other wrong one."""
    assert verify_password(hash_password(PASSWORD), "") is False


def test_verify_rejects_a_malformed_hash():
    """A corrupted stored hash must be refused, not crash the login."""
    assert verify_password("not-an-argon2-hash", PASSWORD) is False

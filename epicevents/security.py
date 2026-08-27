"""Password hashing for the Epic Events CRM."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return the Argon2id hash of a plaintext password."""
    return _hasher.hash(password)


def needs_rehash(password_hash: str) -> bool:
    """Tell whether a stored hash was produced with outdated cost parameters."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except (VerificationError, InvalidHashError):
        return False


def verify_password(password_hash: str, password: str) -> bool:
    """Tell whether a plaintext password matches a stored hash."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False

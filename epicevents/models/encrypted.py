"""Encrypted text columns: encrypted when written, decrypted when read."""

import base64
import binascii

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from epicevents import config
from epicevents.exceptions import ConfigurationError

GENERATE_KEY = (
    'python -c "import base64, os; '
    'print(base64.urlsafe_b64encode(os.urandom(64)).decode())"'
)


def _cipher() -> AESSIV:
    """Return the cipher built from ENCRYPTION_KEY, refusing a missing or bad key."""
    if not config.ENCRYPTION_KEY:
        raise ConfigurationError(
            "ENCRYPTION_KEY is missing from the .env file. "
            f"Generate one with: {GENERATE_KEY}"
        )
    try:
        return AESSIV(base64.urlsafe_b64decode(config.ENCRYPTION_KEY))
    except (binascii.Error, ValueError):
        raise ConfigurationError(
            "ENCRYPTION_KEY is not a valid key. " f"Generate one with: {GENERATE_KEY}"
        ) from None


class EncryptedString(TypeDecorator):
    """A text column stored encrypted, and read back in clear by the application."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt a value on its way to the database."""
        if value is None:
            return None
        encrypted = _cipher().encrypt(value.encode("utf-8"), associated_data=None)
        return base64.urlsafe_b64encode(encrypted).decode("ascii")

    def process_result_value(self, value, dialect):
        """Decrypt a value coming back from the database."""
        if value is None:
            return None
        try:
            decrypted = _cipher().decrypt(
                base64.urlsafe_b64decode(value), associated_data=None
            )
        except (InvalidTag, binascii.Error):
            raise ConfigurationError(
                "A database value cannot be decrypted: "
                "ENCRYPTION_KEY does not match the key used to encrypt it."
            ) from None
        return decrypted.decode("utf-8")

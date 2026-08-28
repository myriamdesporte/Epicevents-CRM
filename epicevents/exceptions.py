"""Custom exceptions for the Epic Events CRM."""


class AuthenticationError(Exception):
    """Raised when the collaborator's identity cannot be established."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when the email and password pair does not match."""


class TokenExpiredError(AuthenticationError):
    """Raised when the session token is past its expiry date."""


class InvalidTokenError(AuthenticationError):
    """Raised when the session token is absent, altered or unreadable."""


class AuthorizationError(Exception):
    """Raised when an identified collaborator lacks the required permission."""

"""Network-related exceptions."""

from .base_exceptions import NemesisError


class NetworkError(NemesisError):
    """Raised when network operations fail."""


class NemesisTimeoutError(NemesisError):
    """Raised when operation times out."""

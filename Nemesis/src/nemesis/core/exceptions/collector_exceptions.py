"""Data collection exceptions."""

from .base_exceptions import NemesisError


class CollectorError(NemesisError):
    """Raised when data collection fails."""

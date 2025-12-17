"""Configuration-related exceptions."""

from .base_exceptions import NemesisError


class ConfigurationError(NemesisError):
    """Raised when configuration is invalid or missing."""


class ValidationError(NemesisError):
    """Raised when validation fails."""

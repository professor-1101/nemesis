"""Reporting-related exceptions."""

from .base_exceptions import NemesisError


class ReportingError(NemesisError):
    """Raised when reporting operations fail."""


class ReportPortalError(ReportingError):
    """Raised when ReportPortal operations fail."""

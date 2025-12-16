"""Browser-related exceptions."""

from .base_exceptions import NemesisError


class BrowserError(NemesisError):
    """Raised when browser operations fail."""


class PageObjectError(NemesisError):
    """Raised when page object operations fail."""


class ElementNotFoundError(PageObjectError):
    """Raised when element is not found on page."""

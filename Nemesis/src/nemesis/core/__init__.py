"""Core package for Nemesis framework - REFACTORED."""

from nemesis.core.browser import BrowserManager, BrowserOperations
from nemesis.core.config import ConfigLoader
# Import exceptions __all__ to avoid duplication
from nemesis.core.exceptions import (
    NemesisError,
    BrowserError,
    PageObjectError,
    ElementNotFoundError,
    ConfigurationError,
    ValidationError,
    ReportingError,
    ReportPortalError,
    NetworkError,
    NemesisTimeoutError,
    TimeoutError,  # Backward compatibility alias
    CollectorError,
)
from nemesis.core.logging import Logger

# Import exception names from exceptions package to maintain compatibility
from nemesis.core.exceptions import __all__ as exceptions_all

__all__ = [
    'BrowserManager', 'BrowserOperations',
    'ConfigLoader',
    'Logger',
] + exceptions_all

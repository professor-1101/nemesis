"""Custom exceptions package."""

from .base_exceptions import NemesisError
from .browser_exceptions import (
    BrowserError, PageObjectError, ElementNotFoundError
)
from .config_exceptions import (
    ConfigurationError, ValidationError
)
from .reporting_exceptions import (
    ReportingError, ReportPortalError
)
from .network_exceptions import (
    NetworkError, NemesisTimeoutError
)
from .collector_exceptions import CollectorError

# Backward compatibility alias
TimeoutError = NemesisTimeoutError

__all__ = [
    'NemesisError',
    'BrowserError', 'PageObjectError', 'ElementNotFoundError',
    'ConfigurationError', 'ValidationError',
    'ReportingError', 'ReportPortalError',
    'NetworkError', 'NemesisTimeoutError',
    'TimeoutError',  # Backward compatibility
    'CollectorError'
]

"""Severity mapping for exception handling."""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import traceback


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExceptionCategory(Enum):
    """Exception categories."""
    TEST_FAILURE = "test_failure"
    TIMEOUT_ERROR = "timeout_error"
    BROWSER_ERROR = "browser_error"
    FRAMEWORK_ERROR = "framework_error"
    CRITICAL_ERROR = "critical_error"


@dataclass
class SeverityMapping:
    """Severity mapping configuration."""
    level: LogLevel
    category: ExceptionCategory
    description: str
    should_retry: bool = False
    should_alert: bool = False
    context_keys: list = None

    def __post_init__(self):
        if self.context_keys is None:
            self.context_keys = []


class SeverityMapper:
    """Maps exceptions to appropriate log levels and categories."""

    def __init__(self):
        """Initialize severity mapper with default mappings."""
        self._mappings = self._create_default_mappings()

    def _create_default_mappings(self) -> Dict[str, SeverityMapping]:
        """Create default severity mappings."""
        return {
            "AssertionError": SeverityMapping(LogLevel.ERROR, ExceptionCategory.TEST_FAILURE, "Test assertion failed", False, True, ["test_id", "scenario", "step"]),
            "TimeoutError": SeverityMapping(LogLevel.WARNING, ExceptionCategory.TIMEOUT_ERROR, "Operation timed out", True, False, ["operation", "timeout_duration"]),
            "ValueError": SeverityMapping(LogLevel.ERROR, ExceptionCategory.FRAMEWORK_ERROR, "Invalid value", False, True, ["value", "expected_type"]),
            "RuntimeError": SeverityMapping(LogLevel.CRITICAL, ExceptionCategory.CRITICAL_ERROR, "Runtime error", False, True, ["component", "operation"])
        }

    def map_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> SeverityMapping:
        """Map exception to severity mapping."""
        exception_name = type(exception).__name__

        if exception_name in self._mappings:
            return self._mappings[exception_name]

        # Default mapping for unknown exceptions
        return SeverityMapping(
            level=LogLevel.ERROR,
            category=ExceptionCategory.CRITICAL_ERROR,
            description=f"Unknown exception: {exception_name}",
            should_retry=False,
            should_alert=True,
            context_keys=["exception_type", "message"]
        )

    def get_exception_context(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get enhanced context for exception logging."""
        mapping = self.map_exception(exception, context)

        exception_context = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "severity_level": mapping.level.value,
            "category": mapping.category.value,
            "description": mapping.description,
            "should_retry": mapping.should_retry,
            "should_alert": mapping.should_alert,
            "traceback": traceback.format_exc()
        }

        # Add context keys if available
        if context:
            for key in mapping.context_keys:
                if key in context:
                    exception_context[key] = context[key]

        return exception_context

"""Base exception classes."""

import traceback
from typing import Any, Dict, Optional


class NemesisError(Exception):
    """Base exception for all Nemesis errors."""

    def __init__(self, message: str, details: str | None = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Initialize exception."""
        self.message = message
        self.details = details
        self.context = context or {}
        self.traceback = traceback.format_exc()
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format exception message with details."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "context": self.context,
            "traceback": self.traceback
        }

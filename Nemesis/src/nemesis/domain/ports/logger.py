"""
ILogger Port - Logging Interface

This port defines the logging contract that infrastructure must implement.
Follows Dependency Inversion Principle: Application depends on this abstraction,
not on concrete logging implementations.

DDD Pattern: Port (Hexagonal Architecture)
Clean Architecture: Domain layer interface for outer layer implementations
"""

from abc import ABC, abstractmethod
from typing import Any


class ILogger(ABC):
    """
    Logger Port Interface

    Defines the contract for logging operations.
    Infrastructure layer provides concrete implementations.
    Application layer depends on this abstraction, maintaining Clean Architecture.

    Methods:
        - debug: Log debug-level message
        - info: Log info-level message
        - warning: Log warning-level message
        - error: Log error-level message
        - critical: Log critical-level message
    """

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log debug message

        Args:
            message: Debug message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log info message

        Args:
            message: Info message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log warning message

        Args:
            message: Warning message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log error message

        Args:
            message: Error message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """
        Log critical message

        Args:
            message: Critical message to log
            **kwargs: Additional context data
        """
        pass

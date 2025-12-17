"""Context manager for correlation and execution tracking."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from contextvars import ContextVar


@dataclass
class LogContext:
    """Log context data structure."""

    correlation_id: Optional[str] = None
    execution_id: Optional[str] = None
    test_id: Optional[str] = None
    scenario: Optional[str] = None
    module: Optional[str] = None
    service_name: Optional[str] = None
    operation_type: Optional[str] = None
    start_time: Optional[str] = None
    custom_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result


class ContextManager:
    """Manages log context and correlation IDs."""

    def __init__(self):
        """Initialize context manager."""
        self._context_var: ContextVar[LogContext] = ContextVar('log_context')
        self._correlation_var: ContextVar[Optional[str]] = ContextVar('correlation_id')
        self._execution_var: ContextVar[Optional[str]] = ContextVar('execution_id')

    def start_correlation(self, **metadata) -> str:
        """Start a new correlation session."""
        correlation_id = str(uuid.uuid4())
        # Use centralized execution ID
        from nemesis.shared.execution_context import ExecutionContext
        execution_id = ExecutionContext.get_execution_id()

        context = LogContext(
            correlation_id=correlation_id,
            execution_id=execution_id,
            start_time=datetime.now(timezone.utc).isoformat(),
            custom_context=metadata
        )
        self._context_var.set(context)
        self._correlation_var.set(correlation_id)
        self._execution_var.set(execution_id)
        return correlation_id

    def end_correlation(self, status: str = "completed", **metadata) -> None:
        """End the current correlation session."""
        context = self._context_var.get(LogContext())
        context.custom_context.update({
            "status": status,
            "end_time": datetime.now(timezone.utc).isoformat(),
            **metadata
        })
        self._context_var.set(LogContext())
        self._correlation_var.set(None)
        self._execution_var.set(None)

    def get_current_context(self) -> LogContext:
        """Get current context."""
        try:
            return self._context_var.get()
        except LookupError:
            return LogContext()

    def get_execution_id(self) -> Optional[str]:
        """Get current execution ID."""
        try:
            return self._execution_var.get()
        except LookupError:
            return None

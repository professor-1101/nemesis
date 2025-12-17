"""Core logger for Nemesis Framework."""

import time
from dataclasses import dataclass

from ..models.log_entry import LogEntry
from ..context.manager import ContextManager
from ..severity.mapper import SeverityMapper
from ..shipping.manager import ShippingManager


@dataclass
class LoggerConfig:
    """Logger configuration."""
    service_name: str
    module: str
    operation_type: str
    log_level: str = "INFO"
    enabled_channels: list = None

    def __post_init__(self):
        if self.enabled_channels is None:
            self.enabled_channels = ["local"]


class Logger:
    """Core logger for structured logging."""

    def __init__(self, config: LoggerConfig, context_manager: ContextManager,
                 severity_mapper: SeverityMapper, shipping_manager: ShippingManager):
        """Initialize logger with dependencies."""
        self.config = config
        self.context_manager = context_manager
        self.severity_mapper = severity_mapper
        self.shipping_manager = shipping_manager

    def _create_log_entry(self, level: str, message: str, **data) -> LogEntry:
        """Create a structured log entry."""
        context = self.context_manager.get_current_context()
        return LogEntry(
            timestamp=time.time(),
            level=level.upper(),
            message=message,
            correlation_id=context.correlation_id,
            execution_id=context.execution_id,
            context=context.to_dict(),
            data=data,
            module=self.config.module,
            service_name=self.config.service_name,
            operation_type=self.config.operation_type
        )

    def _should_log(self, level: str) -> bool:
        """Check if log level should be processed."""
        levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        return levels[level] >= levels[self.config.log_level]

    def _log(self, level: str, message: str, **data) -> None:
        """Internal logging method."""
        if not self._should_log(level):
            return
        log_entry = self._create_log_entry(level, message, **data)
        self.shipping_manager.send_log(log_entry.to_dict(), self.config.enabled_channels)

    def debug(self, message: str, **data) -> None:
        """Log debug message."""
        self._log("DEBUG", message, **data)

    def info(self, message: str, **data) -> None:
        """Log info message."""
        self._log("INFO", message, **data)

    def warning(self, message: str, **data) -> None:
        """Log warning message."""
        self._log("WARNING", message, **data)

    def error(self, message: str, **data) -> None:
        """Log error message."""
        self._log("ERROR", message, **data)

    def critical(self, message: str, **data) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, **data)

    def log_exception(self, exception: Exception, **data) -> None:
        """Log exception with severity mapping."""
        mapping = self.severity_mapper.map_exception(exception)
        context = self.severity_mapper.get_exception_context(exception, data)
        self._log(mapping.level.value, f"Exception: {type(exception).__name__}: {str(exception)}", **context)

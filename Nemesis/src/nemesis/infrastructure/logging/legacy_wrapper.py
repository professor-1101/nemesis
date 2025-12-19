"""Legacy wrapper for backward compatibility."""

from typing import Dict, Any, Optional
from .core.logger import Logger as NewLogger
from .factory import get_factory
from nemesis.domain.ports import ILogger


class Logger(ILogger):
    """Legacy Logger wrapper for backward compatibility."""

    _instance: Optional['Logger'] = None
    _logger: Optional[NewLogger] = None

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize legacy logger."""
        self.config = config or {}
        self._logger = None

    @classmethod
    def get_instance(cls, config: Dict[str, Any] = None) -> 'Logger':
        """Get singleton instance for backward compatibility."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _get_logger(self) -> NewLogger:
        """Get the actual logger instance."""
        if self._logger is None:
            factory = get_factory()
            # Create framework logger for legacy usage
            self._logger = factory.create_framework_logger()
        return self._logger

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._get_logger().info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._get_logger().debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._get_logger().warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._get_logger().error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._get_logger().critical(message, **kwargs)

    def feature_start(self, feature_name: str, **kwargs):
        """Log feature start."""
        self._get_logger().info(f"Feature started: {feature_name}", **kwargs)

    def feature_end(self, feature_name: str, status: str, **kwargs):
        """Log feature end."""
        self._get_logger().info(f"Feature ended: {feature_name} - {status}", **kwargs)

    def scenario_start(self, scenario_name: str, **kwargs):
        """Log scenario start."""
        self._get_logger().info(f"Scenario started: {scenario_name}", **kwargs)

    def scenario_end(self, scenario_name: str, status: str, duration_ms: int = 0, **kwargs):
        """Log scenario end."""
        self._get_logger().info(f"Scenario ended: {scenario_name} - {status} ({duration_ms}ms)", **kwargs)

    def step_start(self, step_name: str, **kwargs):
        """Log step start."""
        self._get_logger().debug(f"Step started: {step_name}", **kwargs)

    def step_end(self, step_name: str, status: str, duration_ms: int = 0, **kwargs):
        """Log step end."""
        self._get_logger().debug(f"Step ended: {step_name} - {status} ({duration_ms}ms)", **kwargs)

    def start_correlation(self, **metadata) -> str:
        """Start correlation for backward compatibility."""
        factory = get_factory()
        context_manager = factory.get_context_manager()
        return context_manager.start_correlation(**metadata)

    def end_correlation(self, status: str = "completed", **metadata):
        """End correlation for backward compatibility."""
        factory = get_factory()
        context_manager = factory.get_context_manager()
        context_manager.end_correlation(status, **metadata)

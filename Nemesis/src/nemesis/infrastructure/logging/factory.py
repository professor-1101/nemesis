"""Factory for creating configured loggers."""

from typing import Optional

from .core.logger import Logger, LoggerConfig
from .context.handler import LoggingContextHandler
from .severity.mapper import SeverityMapper
from .shipping.shipper import LogShipper
from .config.settings import LoggingConfig


class LoggerFactory:
    """Factory for creating configured loggers."""

    def __init__(self):
        """Initialize factory with shared components."""
        self._context_manager = LoggingContextHandler()
        self._severity_mapper = SeverityMapper()
        self._shipping_managers = {}

    def create_test_logger(self, config: Optional[LoggingConfig] = None) -> Logger:
        """Create logger for test execution."""
        if config is None:
            config = LoggingConfig.for_test_execution()

        logger_config = LoggerConfig(
            service_name=config.service_name,
            module=config.module,
            operation_type=config.operation_type,
            log_level=config.log_level,
            enabled_channels=config.enabled_channels
        )

        shipping_manager = self._get_shipping_manager(config)

        return Logger(
            config=logger_config,
            context_manager=self._context_manager,
            severity_mapper=self._severity_mapper,
            shipping_manager=shipping_manager
        )

    def create_framework_logger(self, config: Optional[LoggingConfig] = None) -> Logger:
        """Create logger for framework operations."""
        if config is None:
            config = LoggingConfig.for_framework()

        logger_config = LoggerConfig(
            service_name=config.service_name,
            module=config.module,
            operation_type=config.operation_type,
            log_level=config.log_level,
            enabled_channels=config.enabled_channels
        )

        shipping_manager = self._get_shipping_manager(config)

        return Logger(
            config=logger_config,
            context_manager=self._context_manager,
            severity_mapper=self._severity_mapper,
            shipping_manager=shipping_manager
        )

    def _get_shipping_manager(self, config: LoggingConfig) -> LogShipper:
        """Get or create shipping manager for configuration."""
        config_key = f"{config.service_name}_{config.module}"

        if config_key not in self._shipping_managers:
            self._shipping_managers[config_key] = LogShipper(config)

        return self._shipping_managers[config_key]

    def get_context_manager(self) -> LoggingContextHandler:
        """Get shared context manager."""
        return self._context_manager


# Global factory instance
_factory: Optional[LoggerFactory] = None


def get_factory() -> LoggerFactory:
    """Get global logger factory."""
    global _factory
    if _factory is None:
        _factory = LoggerFactory()
    return _factory


def create_test_logger(config: Optional[LoggingConfig] = None) -> Logger:
    """Create test logger using global factory."""
    return get_factory().create_test_logger(config)


def create_framework_logger(config: Optional[LoggingConfig] = None) -> Logger:
    """Create framework logger using global factory."""
    return get_factory().create_framework_logger(config)

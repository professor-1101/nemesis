"""Collector coordination service for browser data collection.

Initializes and manages console, network, and performance collectors attached to
browser pages. Handles collector lifecycle from initialization to data persistence.
"""

import traceback
from typing import Any

from playwright.sync_api import Page

from nemesis.infrastructure.logging import Logger
from nemesis.shared.execution_context import ExecutionContext


class CollectorCoordinator:
    """
    Manages lifecycle of browser data collectors.

    Initializes console, network, and performance collectors on browser pages,
    provides access to collector instances, and persists collected data to storage.
    Handles all collector errors gracefully to prevent test interruption.
    """

    def __init__(self, logger: Logger | None = None):
        """
        Initialize collector coordinator.

        Args:
            logger: Logger instance for logging (optional, creates if not provided)
        """
        self.logger = logger or Logger.get_instance({})
        self._console_collector: Any | None = None
        self._network_collector: Any | None = None
        self._performance_collector: Any | None = None

    def initialize_collectors(self, page: Page, execution_id: str) -> None:
        """
        Initialize all data collectors.

        Args:
            page: Playwright page instance to attach collectors to
            execution_id: Execution ID for collector context

        Example:
            >>> coordinator = CollectorCoordinator()
            >>> coordinator.initialize_collectors(page, "exec-123")
        """
        try:
            # Lazy import to avoid circular imports
            from nemesis.infrastructure.collectors.console import ConsoleCollector  # pylint: disable=import-outside-toplevel
            from nemesis.infrastructure.collectors.network import NetworkCollector  # pylint: disable=import-outside-toplevel
            from nemesis.infrastructure.collectors.performance import PerformanceCollector  # pylint: disable=import-outside-toplevel

            # Console collector
            self._console_collector = ConsoleCollector(
                page=page,
                filter_levels=["error", "warning", "info"]
            )

            # Network collector
            self._network_collector = NetworkCollector(
                page=page,
                capture_requests=True,
                capture_responses=True
            )

            # Performance collector
            self._performance_collector = PerformanceCollector(
                page=page,
                capture_metrics=True
            )

            self.logger.info("Collectors initialized successfully")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (ImportError, AttributeError, RuntimeError) as e:
            # Collector initialization errors - log but continue
            self.logger.warning(
                f"Failed to initialize collectors: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="CollectorCoordinator",
                method="initialize_collectors"
            )

    def get_console_collector(self) -> Any | None:
        """Get console collector instance."""
        return self._console_collector

    def get_network_collector(self) -> Any | None:
        """Get network collector instance."""
        return self._network_collector

    def get_performance_collector(self) -> Any | None:
        """Get performance collector instance."""
        return self._performance_collector

    def get_all_collectors(self) -> dict[str, Any]:
        """
        Get all collectors as dictionary.

        Returns:
            Dictionary with collector instances
        """
        return {
            'console': self._console_collector,
            'network': self._network_collector,
            'performance': self._performance_collector
        }

    def save_collector_data(self) -> None:
        """
        Save all collector data to persistent storage.

        Retrieves execution ID from environment or ExecutionContext.
        Saves console logs, network metrics, and performance metrics.
        """
        try:
            import os  # pylint: disable=import-outside-toplevel

            # Get execution ID
            execution_id = os.environ.get('NEMESIS_EXECUTION_ID')
            if not execution_id:
                execution_id = ExecutionContext.get_execution_id()

            # Save console logs
            if self._console_collector:
                self._console_collector.save_to_file(execution_id, "console")
                self.logger.info("Console logs saved")

            # Save network data
            if self._network_collector:
                self._network_collector.save_metrics(execution_id, "network_metric")
                self.logger.info("Network metrics saved")

            # Save performance data
            if self._performance_collector:
                self._performance_collector.save_to_file(execution_id, "performance_metric")
                self.logger.info("Performance metrics saved")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (OSError, IOError, AttributeError, RuntimeError) as e:
            # Collector data save errors - log but don't fail
            self.logger.warning(
                f"Failed to save collector data: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="CollectorCoordinator",
                method="save_collector_data"
            )

    def dispose_all(self) -> None:
        """
        Dispose all collectors to free resources.

        Calls dispose() method on collectors that support it.
        """
        try:
            if self._console_collector and hasattr(self._console_collector, "dispose"):
                self._console_collector.dispose()
            if self._network_collector and hasattr(self._network_collector, "dispose"):
                self._network_collector.dispose()
            # Performance collector is pull-based; no listeners to detach

            # Clear references
            self._console_collector = None
            self._network_collector = None
            self._performance_collector = None

            self.logger.debug("All collectors disposed")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (AttributeError, RuntimeError) as e:
            self.logger.debug(
                f"Collector dispose error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="CollectorCoordinator",
                method="dispose_all"
            )

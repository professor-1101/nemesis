"""Accessor for collector data from environment context.

Responsibilities:
- Retrieve network, console, and performance collector data
- Handle environment manager access
- Provide unified interface for collector access
"""
from typing import Any, Optional

from nemesis.infrastructure.logging import Logger


class CollectorsAccessor:
    """Provides access to collector data from environment context."""

    def __init__(self) -> None:
        """Initialize collectors accessor."""
        self.logger = Logger.get_instance({})

    def get_collector_data(self, collector_type: str) -> Optional[Any]:
        """
        Get collector data from environment context.

        Args:
            collector_type: Type of collector ('network', 'console', 'performance')

        Returns:
            Collector data if available, None otherwise
        """
        try:
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()

            if not env_manager or not hasattr(env_manager, 'context'):
                return None

            context = env_manager.context

            # Get collector based on type
            if collector_type == 'network':
                if hasattr(context, 'network_collector'):
                    network_collector = context.network_collector
                    if network_collector and hasattr(network_collector, 'get_collected_data'):
                        return network_collector.get_collected_data()

            elif collector_type == 'console':
                if hasattr(context, 'console_collector'):
                    console_collector = context.console_collector
                    if console_collector and hasattr(console_collector, 'get_collected_data'):
                        return console_collector.get_collected_data()

            elif collector_type == 'performance':
                if hasattr(context, 'performance_collector'):
                    perf_collector = context.performance_collector
                    if perf_collector and hasattr(perf_collector, 'get_metrics'):
                        return perf_collector.get_metrics()

            return None

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.debug(
                f"Failed to get {collector_type} collector data: {e}",
                module=__name__,
                class_name="CollectorsAccessor",
                method="get_collector_data"
            )
            return None

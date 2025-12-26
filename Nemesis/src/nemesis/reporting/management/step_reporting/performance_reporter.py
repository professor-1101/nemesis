"""Performance reporter for step-level reporting.

Responsibilities:
- Attach performance metrics as files
- Handle performance data collection
"""
import json
from datetime import datetime
from typing import Any

from nemesis.infrastructure.logging import Logger
from .collectors_accessor import CollectorsAccessor


class PerformanceReporter:
    """Handles performance metrics reporting for step reporting."""

    def __init__(self, collectors_accessor: CollectorsAccessor) -> None:
        """
        Initialize performance reporter.

        Args:
            collectors_accessor: Accessor for collector data
        """
        self.logger = Logger.get_instance({})
        self.collectors = collectors_accessor

    def attach_performance_metrics(self, rp_client: Any, step_name: str) -> None:
        """
        Attach performance metrics collected during the step.

        Args:
            rp_client: ReportPortal client
            step_name: Name of the step
        """
        try:
            # Get performance collector data
            perf_collector = self.collectors.get_collector_data('performance')
            if perf_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                name = f"performance_{timestamp}"

                # Convert to JSON and attach
                perf_json = json.dumps(perf_collector, indent=2)
                rp_client.attach_file(
                    perf_json.encode('utf-8'),
                    f"Performance Metrics: {step_name}",
                    "performance_metrics"
                )
                self.logger.debug(f"Performance metrics attached: {len(perf_json)} bytes")

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to attach performance metrics: {e}",
                module=__name__,
                class_name="PerformanceReporter",
                method="attach_performance_metrics"
            )

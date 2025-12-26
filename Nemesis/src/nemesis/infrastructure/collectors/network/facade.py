"""Network Collector Facade - Main interface implementing ICollector.

Orchestrates network event collection, metrics calculation, HAR export, and reporting.
This is the main entry point that other modules should use.
"""
from pathlib import Path
from typing import Any, Dict, List

from playwright.sync_api import Page

from nemesis.domain.ports import ICollector
from nemesis.infrastructure.collectors.base_collector import BaseCollector
from .event_collector import NetworkEventCollector
from .metrics_calculator import NetworkMetricsCalculator
from .har_exporter import HARExporter
from .report_writer import NetworkReportWriter


class NetworkCollectorFacade(ICollector, BaseCollector):
    """
    Facade for network collection operations implementing ICollector port.

    This class orchestrates:
    - NetworkEventCollector: Captures network events
    - NetworkMetricsCalculator: Calculates aggregated metrics (optimized O(n))
    - HARExporter: Exports to HAR 1.2 format
    - NetworkReportWriter: Persists data to files

    Responsibilities (Single Responsibility Principle):
    - Coordinate between specialized components
    - Implement ICollector interface
    - Provide backward compatibility with existing code

    Example:
        >>> with NetworkCollectorFacade(page) as collector:
        ...     collector.start()
        ...     # Run tests
        ...     collector.stop()
        ...     path = collector.save_collected_data(execution_id, output_dir)
    """

    def __init__(
        self,
        page: Page,
        url_filter: str | None = None,
        capture_requests: bool = True,
        capture_responses: bool = True
    ) -> None:
        """
        Initialize network collector facade.

        Args:
            page: Playwright page instance
            url_filter: Optional URL substring filter
            capture_requests: Whether to capture request events
            capture_responses: Whether to capture response events
        """
        # Initialize specialized components
        self.event_collector = NetworkEventCollector(
            page, url_filter, capture_requests, capture_responses
        )
        self.metrics_calculator = NetworkMetricsCalculator()
        self.har_exporter = HARExporter()
        self.report_writer = NetworkReportWriter()

        # Start collection if capture flags are set
        if capture_requests or capture_responses:
            self.event_collector.start_collection()

    # ICollector interface implementation
    def start(self) -> None:
        """Start collecting network data."""
        self.event_collector.start_collection()

    def stop(self) -> None:
        """Stop collecting network data."""
        self.event_collector.stop_collection()

    def get_collected_data(self) -> List[Dict[str, Any]]:
        """
        Get collected network requests/responses.

        Returns:
            List of network event dictionaries
        """
        return self.event_collector.get_collected_data()

    def save_collected_data(
        self,
        execution_id: str,
        output_dir: Path,
        scenario_name: str = ""
    ) -> Path:
        """
        Save collected data to file.

        Args:
            execution_id: Unique execution identifier
            output_dir: Output directory path (not used - PathManager handles paths)
            scenario_name: Scenario name (not used currently)

        Returns:
            Path to saved JSON metrics file
        """
        return self.save_metrics(execution_id, scenario_name)

    def clear(self) -> None:
        """Clear collected data."""
        self.event_collector.clear_collected_data()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dictionary containing network metrics
        """
        return self.get_metrics()

    # Public methods for backward compatibility
    def get_metrics(self) -> dict[str, Any]:
        """
        Get network metrics summary.

        Uses optimized single-pass calculation (O(n) instead of O(5n)).

        Returns:
            Dictionary containing:
            - total_requests: Count of request events
            - total_responses: Count of response events
            - total_failed: Count of failed events
            - status_codes: Distribution of HTTP status codes
            - avg_duration_ms: Average response duration
            - total_size_bytes: Total data transferred
            - requests: Copy of raw data
        """
        collected_data = self.event_collector.get_collected_data()
        return self.metrics_calculator.calculate_metrics(collected_data)

    def export_as_har(self) -> dict[str, Any]:
        """
        Export network data as HAR (HTTP Archive) 1.2 format.

        HAR format is compatible with Chrome DevTools, Firefox DevTools,
        and other network analysis tools.

        Returns:
            HAR 1.2 formatted dictionary

        Reference: http://www.softwareishard.com/blog/har-12-spec/
        """
        collected_data = self.event_collector.get_collected_data()
        return self.har_exporter.export(collected_data)

    def save_metrics(self, execution_id: str, _scenario_name: str) -> Path:
        """
        Save network metrics to JSON and HAR formats.

        Saves two files:
        1. network_metric.json - Custom format with Nemesis metrics
        2. network.har - Standard HAR 1.2 format (importable to Chrome DevTools)

        Args:
            execution_id: Unique execution identifier
            _scenario_name: Scenario name (not used currently)

        Returns:
            Path to JSON metrics file
        """
        metrics = self.get_metrics()
        har_data = self.export_as_har()
        return self.report_writer.save_metrics(metrics, har_data, execution_id)

    def dispose(self) -> None:
        """Detach all network listeners explicitly."""
        self.event_collector.stop_collection()

    def _cleanup_listeners(self) -> None:
        """Clean up network listeners (called by BaseCollector context manager)."""
        self.event_collector.stop_collection()

"""Network collectors package - refactored for Single Responsibility Principle.

This package provides network request/response collection capabilities with:
- Event collection from Playwright
- Metrics calculation (optimized O(n))
- HAR 1.2 format export
- File persistence

Architecture:
- NetworkEventCollector: Captures network events
- NetworkMetricsCalculator: Calculates metrics (single-pass O(n))
- HARExporter: Exports to HAR 1.2 format
- NetworkReportWriter: Persists to files
- NetworkCollectorFacade: Main interface (implements ICollector)

Usage:
    >>> from nemesis.infrastructure.collectors.network import NetworkCollector
    >>> collector = NetworkCollector(page)
    >>> collector.start()
    >>> # ... run tests ...
    >>> metrics = collector.get_metrics()
    >>> path = collector.save_metrics(execution_id, scenario_name)

For backward compatibility, NetworkCollector is an alias to NetworkCollectorFacade.
"""
from .facade import NetworkCollectorFacade
from .event_collector import NetworkEventCollector
from .metrics_calculator import NetworkMetricsCalculator
from .har_exporter import HARExporter
from .report_writer import NetworkReportWriter

# Main interface - use this for backward compatibility
NetworkCollector = NetworkCollectorFacade

__all__ = [
    "NetworkCollector",  # Main interface (facade)
    "NetworkCollectorFacade",
    "NetworkEventCollector",
    "NetworkMetricsCalculator",
    "HARExporter",
    "NetworkReportWriter",
]

"""Step reporting package - refactored for Single Responsibility Principle.

This package provides step-level reporting capabilities with:
- Step lifecycle management (start/end)
- Placeholder replacement in step names
- Network activity logging and attachment
- Console logs logging and attachment
- Performance metrics attachment

Architecture:
- CollectorsAccessor: Unified collector data access
- StepDataProcessor: Placeholder replacement and metadata extraction
- NetworkDataFormatter: Network data formatting as ASCII tables
- ConsoleDataFormatter: Console logs formatting with emoji indicators
- NetworkReporter: Network activity reporting
- ConsoleReporter: Console logs reporting
- PerformanceReporter: Performance metrics reporting
- StepHandlerFacade: Main interface (orchestrates all components)

Usage:
    >>> from nemesis.reporting.management.step_reporting import StepHandler
    >>> handler = StepHandler(reporter_manager)
    >>> handler.start_step(step)
    >>> # ... step execution ...
    >>> handler.end_step(step, duration)

For backward compatibility, StepHandler is an alias to StepHandlerFacade.
"""
from .step_handler_facade import StepHandlerFacade
from .collectors_accessor import CollectorsAccessor
from .data_processor import StepDataProcessor
from .network_formatter import NetworkDataFormatter
from .console_formatter import ConsoleDataFormatter
from .network_reporter import NetworkReporter
from .console_reporter import ConsoleReporter
from .performance_reporter import PerformanceReporter

# Main interface - use this for backward compatibility
StepHandler = StepHandlerFacade

__all__ = [
    "StepHandler",  # Main interface (facade)
    "StepHandlerFacade",
    "CollectorsAccessor",
    "StepDataProcessor",
    "NetworkDataFormatter",
    "ConsoleDataFormatter",
    "NetworkReporter",
    "ConsoleReporter",
    "PerformanceReporter",
]

"""Step management for reporting.

This module provides backward compatibility by importing from the refactored
step_reporting package.

The original 763-line StepHandler class has been refactored into specialized
components following the Single Responsibility Principle:

- CollectorsAccessor: Unified collector data access
- StepDataProcessor: Placeholder replacement and metadata extraction
- NetworkDataFormatter: Network data formatting
- ConsoleDataFormatter: Console logs formatting
- NetworkReporter: Network activity reporting
- ConsoleReporter: Console logs reporting
- PerformanceReporter: Performance metrics reporting
- StepHandlerFacade: Main coordinator

For the legacy implementation, see step_handler_legacy.py
"""

# Import from refactored package
from .step_reporting import (
    StepHandler,
    StepHandlerFacade,
    CollectorsAccessor,
    StepDataProcessor,
    NetworkDataFormatter,
    ConsoleDataFormatter,
    NetworkReporter,
    ConsoleReporter,
    PerformanceReporter,
)

__all__ = [
    "StepHandler",  # Main interface (maintains backward compatibility)
    "StepHandlerFacade",
    "CollectorsAccessor",
    "StepDataProcessor",
    "NetworkDataFormatter",
    "ConsoleDataFormatter",
    "NetworkReporter",
    "ConsoleReporter",
    "PerformanceReporter",
]

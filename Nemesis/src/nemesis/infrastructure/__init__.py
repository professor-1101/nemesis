"""
Nemesis Infrastructure Layer

This layer contains adapters that implement domain ports (interfaces).
Infrastructure depends on Domain layer but Domain is independent of Infrastructure.

Clean Architecture:
- Implements Domain ports (interfaces)
- Contains framework-specific code (Playwright, SigNoz, etc.)
- Can be swapped without changing Domain or Application layers

Adapters:
- Browser: PlaywrightBrowserDriver (implements IBrowserDriver)
- Reporting: JSONReporter, ConsoleReporter (implements IReporter)
- Logging: SigNozShipper, LocalFileShipper (implements ILogShipper)
- Collectors: ConsoleCollector, NetworkCollector (implements ICollector)
"""

# Browser Adapters
from .browser.playwright_adapter import PlaywrightBrowserDriver

# Reporting Adapters
from .reporting.json_reporter import JSONReporter
from .reporting.console_reporter import ConsoleReporter

# Logging Adapters
from .logging.signoz_shipper import SigNozShipper
from .logging.local_file_shipper import LocalFileShipper

__all__ = [
    # Browser
    "PlaywrightBrowserDriver",
    # Reporting
    "JSONReporter",
    "ConsoleReporter",
    # Logging
    "SigNozShipper",
    "LocalFileShipper",
]

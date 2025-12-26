"""Playwright Adapter - Implementation of IBrowserDriver.

DEPRECATED: This module is maintained for backward compatibility only.
New code should import from:
    from nemesis.infrastructure.browser.playwright_adapters import (
        PlaywrightPageAdapter,
        PlaywrightBrowserAdapter,
        PlaywrightBrowserDriver
    )

This adapter has been refactored into a package with specialized classes:
- SensitiveDataMasker: Handles sensitive data detection and masking
- ElementInspector: Extracts element details using JavaScript
- ElementFormatter: Formats element info for readable logs
- ActionLogger: Coordinates action logging
- PlaywrightPageAdapter: Main page adapter (facade)
- PlaywrightBrowserAdapter: Browser adapter
- PlaywrightBrowserDriver: Driver adapter

The refactoring follows Single Responsibility Principle (SRP) for better
maintainability, testability, and clarity.
"""

# Re-export classes for backward compatibility
from .playwright_adapters import (
    PlaywrightPageAdapter,
    PlaywrightBrowserAdapter,
    PlaywrightBrowserDriver,
    SensitiveDataMasker,
    ElementInspector,
    ElementFormatter,
    ActionLogger,
)

__all__ = [
    "PlaywrightPageAdapter",
    "PlaywrightBrowserAdapter",
    "PlaywrightBrowserDriver",
    "SensitiveDataMasker",
    "ElementInspector",
    "ElementFormatter",
    "ActionLogger",
]

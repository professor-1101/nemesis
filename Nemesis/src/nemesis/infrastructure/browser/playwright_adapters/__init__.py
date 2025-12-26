"""Playwright Adapters - Refactored for Single Responsibility Principle.

This package provides Playwright implementations of browser interfaces with:
- Sensitive data masking in action logs
- Enhanced element inspection for debugging
- Structured action logging for ReportPortal
- Clean separation of concerns

Architecture:
- SensitiveDataMasker: Detects and masks sensitive data in logs
- ElementInspector: Extracts detailed element information via JavaScript
- ElementFormatter: Formats element info for readable logs
- ActionLogger: Coordinates action logging with masking and formatting
- PlaywrightPageAdapter: Main page adapter (facade for action logging)
- PlaywrightBrowserAdapter: Browser adapter with context management
- PlaywrightBrowserDriver: Driver adapter for browser lifecycle

Usage:
    >>> from nemesis.infrastructure.browser.playwright_adapters import PlaywrightBrowserDriver
    >>> driver = PlaywrightBrowserDriver()
    >>> browser = driver.launch(headless=True)
    >>> page = browser.new_page()
    >>> page.goto("https://example.com")

For backward compatibility, classes are exported at package level.
"""

# Specialized components
from .sensitive_data_masker import SensitiveDataMasker
from .element_inspector import ElementInspector
from .element_formatter import ElementFormatter
from .action_logger import ActionLogger

# Main adapters
from .playwright_page_adapter import PlaywrightPageAdapter
from .playwright_browser_adapter import PlaywrightBrowserAdapter
from .playwright_driver import PlaywrightBrowserDriver

__all__ = [
    # Specialized components
    "SensitiveDataMasker",
    "ElementInspector",
    "ElementFormatter",
    "ActionLogger",
    # Main adapters (primary interfaces)
    "PlaywrightPageAdapter",
    "PlaywrightBrowserAdapter",
    "PlaywrightBrowserDriver",
]

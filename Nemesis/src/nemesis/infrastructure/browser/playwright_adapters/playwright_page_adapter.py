"""Playwright Page Adapter - Implementation of IPage interface.

Responsibilities:
- Adapt Playwright Page to domain's IPage interface
- Coordinate action logging with specialized components
- Delegate to masker, inspector, formatter, and logger
"""
from typing import Any, Callable, Optional, List
from playwright.sync_api import Page

from nemesis.domain.ports import IPage
from nemesis.infrastructure.logging import Logger

from .sensitive_data_masker import SensitiveDataMasker
from .element_inspector import ElementInspector
from .element_formatter import ElementFormatter
from .action_logger import ActionLogger


class PlaywrightPageAdapter(IPage):
    """
    Adapter: Wraps Playwright Page to implement IPage interface.

    This allows domain/application code to use IPage without knowing about Playwright.

    Coordinates specialized components:
    - SensitiveDataMasker: Handles sensitive data masking
    - ElementInspector: Extracts element details
    - ElementFormatter: Formats element info for logs
    - ActionLogger: Coordinates action logging
    """

    def __init__(
        self,
        playwright_page: Page,
        sensitive_patterns: Optional[List[str]] = None,
        mask_character: str = "***"
    ):
        """
        Initialize adapter with Playwright page.

        Args:
            playwright_page: Actual Playwright Page instance
            sensitive_patterns: List of patterns for sensitive data masking (case-insensitive)
            mask_character: Character/string to use for masking sensitive data
        """
        self._page = playwright_page
        self._logger = Logger.get_instance({})

        # Initialize specialized components
        self._masker = SensitiveDataMasker(sensitive_patterns, mask_character)
        self._inspector = ElementInspector()
        self._formatter = ElementFormatter()
        self._action_logger = ActionLogger(self._masker, self._inspector, self._formatter)

    def set_action_logger(self, logger_callback: Callable[[str], None]) -> None:
        """
        Set callback for logging actions to ReportPortal.

        Args:
            logger_callback: Function that takes action message and logs it
        """
        self._action_logger.set_action_logger(logger_callback)

    def goto(self, url: str, **options) -> None:
        """
        Navigate to URL.

        Args:
            url: Target URL
            **options: Additional Playwright navigation options
        """
        self._action_logger.log_action(
            page=None,  # No element inspection for navigation
            action="NAVIGATE",
            details=f"URL: {url}"
        )
        self._page.goto(url, **options)

    def click(self, selector: str, **options) -> None:
        """
        Click element.

        Args:
            selector: CSS/XPath selector
            **options: Additional Playwright click options
        """
        self._action_logger.log_action(
            page=self._page,
            action="CLICK",
            selector=selector
        )
        self._page.click(selector, **options)

    def fill(self, selector: str, value: str, **options) -> None:
        """
        Fill input field.

        Args:
            selector: CSS/XPath selector for input element
            value: Value to fill (will be masked if selector indicates sensitive data)
            **options: Additional Playwright fill options
        """
        self._action_logger.log_action(
            page=self._page,
            action="FILL",
            selector=selector,
            value=value
        )
        self._page.fill(selector, value, **options)

    def get_text(self, selector: str) -> str:
        """
        Get element text content.

        Args:
            selector: CSS/XPath selector

        Returns:
            Text content of element
        """
        self._action_logger.log_action(
            page=self._page,
            action="GET_TEXT",
            selector=selector
        )
        result = self._page.text_content(selector) or ""

        # Log result
        self._action_logger.log_action(
            page=None,
            action="TEXT_RETRIEVED",
            details=f"Length: {len(result)} chars"
        )
        return result

    def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible.

        Args:
            selector: CSS/XPath selector

        Returns:
            True if element is visible, False otherwise
        """
        self._action_logger.log_action(
            page=self._page,
            action="CHECK_VISIBILITY",
            selector=selector
        )
        result = self._page.is_visible(selector)

        # Log result
        self._action_logger.log_action(
            page=None,
            action="VISIBILITY_RESULT",
            details=f"Visible: {result}"
        )
        return result

    def screenshot(self, **options) -> bytes:
        """
        Take screenshot of page.

        Args:
            **options: Playwright screenshot options (path, full_page, etc.)

        Returns:
            Screenshot as bytes
        """
        options_str = ", ".join(f"{k}={v}" for k, v in options.items()) if options else "default"
        self._action_logger.log_action(
            page=None,
            action="SCREENSHOT",
            details=f"Options: {options_str}"
        )
        return self._page.screenshot(**options)

    def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in page context.

        Args:
            script: JavaScript code to execute

        Returns:
            Result of JavaScript execution
        """
        # Truncate long scripts in logs
        script_preview = script[:100] + "..." if len(script) > 100 else script
        self._action_logger.log_action(
            page=None,
            action="EXECUTE_JAVASCRIPT",
            details=f"Script: {script_preview}"
        )
        result = self._page.evaluate(script)

        # Log result type
        self._action_logger.log_action(
            page=None,
            action="JAVASCRIPT_RESULT",
            details=f"Type: {type(result).__name__}"
        )
        return result

    def on(self, event: str, handler: callable) -> None:
        """
        Add event listener.

        Args:
            event: Event name (e.g., 'console', 'request', 'response')
            handler: Callback function for event

        Note:
            This method is not logged to avoid noise in logs
        """
        self._page.on(event, handler)

    def close(self) -> None:
        """Close page and cleanup resources."""
        self._action_logger.log_action(
            page=None,
            action="CLOSE_PAGE",
            details="Closing page and releasing resources"
        )
        self._page.close()

    # Expose underlying Playwright page for advanced usage
    @property
    def playwright_page(self) -> Page:
        """Get underlying Playwright page (for advanced usage only)."""
        return self._page

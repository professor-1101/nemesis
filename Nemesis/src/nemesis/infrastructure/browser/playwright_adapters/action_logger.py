"""Action Logger for Playwright adapters.

Responsibilities:
- Log browser actions with enhanced details
- Coordinate logging to console and ReportPortal
- Integrate with masker, inspector, and formatter
"""
from typing import Callable, Optional
from playwright.sync_api import Page

from nemesis.infrastructure.logging import Logger
from .sensitive_data_masker import SensitiveDataMasker
from .element_inspector import ElementInspector
from .element_formatter import ElementFormatter


class ActionLogger:
    """Handles action logging for Playwright adapters."""

    def __init__(
        self,
        masker: SensitiveDataMasker,
        inspector: ElementInspector,
        formatter: ElementFormatter
    ) -> None:
        """
        Initialize action logger.

        Args:
            masker: Sensitive data masker instance
            inspector: Element inspector instance
            formatter: Element formatter instance
        """
        self._logger = Logger.get_instance({})
        self._masker = masker
        self._inspector = inspector
        self._formatter = formatter
        self._action_logger: Optional[Callable[[str], None]] = None

    def set_action_logger(self, logger_callback: Callable[[str], None]) -> None:
        """
        Set callback for logging actions to ReportPortal.

        Args:
            logger_callback: Function that takes action message and logs it
        """
        self._action_logger = logger_callback

    def log_action(
        self,
        page: Optional[Page],
        action: str,
        selector: str = "",
        value: str = "",
        details: str = ""
    ) -> None:
        """
        Log action with enhanced element details and structured formatting.

        This method creates comprehensive action logs that include:
        - Action type (CLICK, FILL, NAVIGATE, etc.)
        - Selector used
        - Element details (tag, type, role, aria-label, text)
        - Values (masked if sensitive)
        - Additional context

        Args:
            page: Playwright page instance (optional for navigation logs)
            action: Action name (e.g., "CLICK", "FILL", "NAVIGATE")
            selector: CSS/XPath selector (optional)
            value: Value for fill actions (optional, will be masked if sensitive)
            details: Additional details (optional)

        Note:
            Logging failures are caught and logged as warnings to prevent
            breaking test execution.
        """
        try:
            # Build structured message
            message_parts = [f"[ACTION] {action}"]

            # Add selector
            if selector:
                message_parts.append(f"Selector: {selector}")

                # Get and format element details (only if page is available)
                if page:
                    element_info = self._inspector.get_element_details(page, selector)
                    if element_info:
                        element_str = self._formatter.format_element_info(element_info)
                        message_parts.append(f"Element: {element_str}")

            # Add value (with masking for sensitive data)
            if value:
                masked_value = self._masker.mask_sensitive_value(value, selector)
                message_parts.append(f"Value: {masked_value}")

            # Add additional details
            if details:
                message_parts.append(f"Details: {details}")

            # Join message parts
            message = " | ".join(message_parts)

            # Log to local logger
            self._logger.info(f"[ACTION LOG] {message}")

            # Log to ReportPortal if callback is set
            if self._action_logger:
                self._logger.debug(f"[ACTION RP] Sending to ReportPortal: {message}")
                self._action_logger(message)

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Don't let logging failures break tests
            self._logger.warning(f"Failed to log action '{action}': {e}")

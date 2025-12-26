"""Element Inspector for Playwright adapters.

Responsibilities:
- Extract detailed element information for enhanced logging
- Execute JavaScript to gather element properties
"""
from typing import Any, Dict
from playwright.sync_api import Page

from nemesis.infrastructure.logging import Logger


class ElementInspector:
    """Handles element inspection for detailed action logging."""

    def __init__(self) -> None:
        """Initialize element inspector."""
        self._logger = Logger.get_instance({})

    def get_element_details(self, page: Page, selector: str) -> Dict[str, Any]:
        """
        Extract detailed element information for enhanced logging.

        This method introspects the target element to provide rich context
        in action logs, making debugging and analysis much easier.

        Args:
            page: Playwright page instance
            selector: CSS/XPath selector for the element

        Returns:
            Dictionary with element details:
            - tag: HTML tag name (e.g., 'button', 'input')
            - type: Input type attribute (e.g., 'text', 'password', 'email')
            - role: ARIA role attribute
            - aria_label: ARIA label for accessibility
            - text: Visible text content (truncated to 50 chars)
            - id: Element ID attribute
            - name: Element name attribute
            - placeholder: Input placeholder text

        Note:
            If element is not found or any error occurs, returns empty dict
            to prevent logging from breaking test execution.
        """
        try:
            # Get locator for element
            locator = page.locator(selector).first

            # Wait briefly for element (non-blocking)
            if not locator.count():
                return {}

            # Extract element properties using JavaScript for efficiency
            # This single evaluate call is faster than multiple get_attribute calls
            element_info = page.evaluate(
                """(selector) => {
                    const element = document.querySelector(selector);
                    if (!element) return {};

                    return {
                        tag: element.tagName.toLowerCase(),
                        type: element.getAttribute('type') || '',
                        role: element.getAttribute('role') || '',
                        aria_label: element.getAttribute('aria-label') || '',
                        text: element.innerText || element.textContent || '',
                        id: element.getAttribute('id') || '',
                        name: element.getAttribute('name') || '',
                        placeholder: element.getAttribute('placeholder') || '',
                        class: element.getAttribute('class') || '',
                        visible: !element.hidden &&
                                element.offsetParent !== null &&
                                window.getComputedStyle(element).display !== 'none'
                    };
                }""",
                selector
            )

            # Truncate text content to reasonable length
            if element_info.get('text'):
                text = element_info['text'].strip()
                element_info['text'] = text[:50] + ('...' if len(text) > 50 else '')

            return element_info

        except Exception as e:
            # Log debug info but don't break execution
            self._logger.debug(f"Could not extract element details for '{selector}': {e}")
            return {}

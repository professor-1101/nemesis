"""Playwright Adapter - Implementation of IBrowserDriver

This adapter wraps Playwright to implement the domain's IBrowserDriver interface.
This allows the domain to be independent of Playwright.
"""

from typing import Optional, List, Any, Callable, Dict
from pathlib import Path
import inspect
import re

from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
    Locator,
)

from nemesis.domain.ports import IBrowserDriver, IBrowser, IPage
from nemesis.infrastructure.logging import Logger


class PlaywrightPageAdapter(IPage):
    """
    Adapter: Wraps Playwright Page to implement IPage interface

    This allows domain/application code to use IPage without knowing about Playwright.
    """

    # Default sensitive patterns for masking
    DEFAULT_SENSITIVE_PATTERNS = [
        "password", "passwd", "pwd",
        "token", "api_key", "apikey",
        "secret", "auth", "authorization"
    ]

    def __init__(
        self,
        playwright_page: Page,
        sensitive_patterns: Optional[List[str]] = None,
        mask_character: str = "***"
    ):
        """
        Initialize adapter with Playwright page

        Args:
            playwright_page: Actual Playwright Page instance
            sensitive_patterns: List of patterns for sensitive data masking (case-insensitive)
            mask_character: Character/string to use for masking sensitive data
        """
        self._page = playwright_page
        self._logger = Logger.get_instance({})
        self._action_logger: Optional[Callable[[str], None]] = None

        # Sensitive data masking configuration
        self._sensitive_patterns = sensitive_patterns or self.DEFAULT_SENSITIVE_PATTERNS
        self._mask_character = mask_character

    def set_action_logger(self, logger_callback: Callable[[str], None]) -> None:
        """
        Set callback for logging actions to ReportPortal

        Args:
            logger_callback: Function that takes action message and logs it
        """
        self._action_logger = logger_callback

    def _is_sensitive_selector(self, selector: str) -> bool:
        """
        Check if selector contains sensitive data patterns

        Args:
            selector: CSS/XPath selector

        Returns:
            True if selector matches any sensitive pattern
        """
        selector_lower = selector.lower()
        return any(
            pattern.lower() in selector_lower
            for pattern in self._sensitive_patterns
        )

    def _mask_sensitive_value(self, value: str, selector: str = "") -> str:
        """
        Mask sensitive values based on selector patterns

        Args:
            value: Value to potentially mask
            selector: Selector that may indicate sensitive data

        Returns:
            Original value or masked value if sensitive
        """
        if self._is_sensitive_selector(selector):
            return self._mask_character
        return value

    def _get_element_details(self, selector: str) -> Dict[str, Any]:
        """
        Extract detailed element information for enhanced logging

        This method introspects the target element to provide rich context
        in action logs, making debugging and analysis much easier.

        Args:
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
            locator: Locator = self._page.locator(selector).first

            # Wait briefly for element (non-blocking)
            if not locator.count():
                return {}

            # Extract element properties using JavaScript for efficiency
            # This single evaluate call is faster than multiple get_attribute calls
            element_info = self._page.evaluate(
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

    def _format_element_info(self, element_info: Dict[str, Any]) -> str:
        """
        Format element information for readable logging

        Args:
            element_info: Dictionary with element details

        Returns:
            Formatted string with key element attributes
        """
        if not element_info:
            return ""

        parts = []

        # Tag name with type (most important)
        tag = element_info.get('tag', 'unknown')
        elem_type = element_info.get('type', '')

        if elem_type:
            parts.append(f"<{tag}[type={elem_type}]>")
        else:
            parts.append(f"<{tag}>")

        # ID (very useful for identification)
        elem_id = element_info.get('id', '')
        if elem_id:
            parts.append(f"id=\"{elem_id}\"")

        # Name attribute (common for forms)
        elem_name = element_info.get('name', '')
        if elem_name:
            parts.append(f"name=\"{elem_name}\"")

        # ARIA label (accessibility & identification)
        aria_label = element_info.get('aria_label', '')
        if aria_label:
            parts.append(f"aria-label=\"{aria_label}\"")

        # Role (accessibility context)
        role = element_info.get('role', '')
        if role:
            parts.append(f"role=\"{role}\"")

        # Text content (what user sees)
        text = element_info.get('text', '')
        if text:
            parts.append(f"text=\"{text}\"")

        # Placeholder (for inputs)
        placeholder = element_info.get('placeholder', '')
        if placeholder:
            parts.append(f"placeholder=\"{placeholder}\"")

        return " | ".join(parts)

    def _log_action(
        self,
        action: str,
        selector: str = "",
        value: str = "",
        details: str = ""
    ) -> None:
        """
        Log action with enhanced element details and structured formatting

        This method creates comprehensive action logs that include:
        - Action type (CLICK, FILL, NAVIGATE, etc.)
        - Selector used
        - Element details (tag, type, role, aria-label, text)
        - Values (masked if sensitive)
        - Additional context

        Args:
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

                # Get and format element details
                element_info = self._get_element_details(selector)
                if element_info:
                    element_str = self._format_element_info(element_info)
                    message_parts.append(f"Element: {element_str}")

            # Add value (with masking for sensitive data)
            if value:
                masked_value = self._mask_sensitive_value(value, selector)
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

    def goto(self, url: str, **options) -> None:
        """
        Navigate to URL

        Args:
            url: Target URL
            **options: Additional Playwright navigation options
        """
        self._log_action(
            action="NAVIGATE",
            details=f"URL: {url}"
        )
        self._page.goto(url, **options)

    def click(self, selector: str, **options) -> None:
        """
        Click element

        Args:
            selector: CSS/XPath selector
            **options: Additional Playwright click options
        """
        self._log_action(
            action="CLICK",
            selector=selector
        )
        self._page.click(selector, **options)

    def fill(self, selector: str, value: str, **options) -> None:
        """
        Fill input field

        Args:
            selector: CSS/XPath selector for input element
            value: Value to fill (will be masked if selector indicates sensitive data)
            **options: Additional Playwright fill options
        """
        self._log_action(
            action="FILL",
            selector=selector,
            value=value
        )
        self._page.fill(selector, value, **options)

    def get_text(self, selector: str) -> str:
        """
        Get element text content

        Args:
            selector: CSS/XPath selector

        Returns:
            Text content of element
        """
        self._log_action(
            action="GET_TEXT",
            selector=selector
        )
        result = self._page.text_content(selector) or ""

        # Log result
        self._log_action(
            action="TEXT_RETRIEVED",
            details=f"Length: {len(result)} chars"
        )
        return result

    def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible

        Args:
            selector: CSS/XPath selector

        Returns:
            True if element is visible, False otherwise
        """
        self._log_action(
            action="CHECK_VISIBILITY",
            selector=selector
        )
        result = self._page.is_visible(selector)

        # Log result
        self._log_action(
            action="VISIBILITY_RESULT",
            details=f"Visible: {result}"
        )
        return result

    def screenshot(self, **options) -> bytes:
        """
        Take screenshot of page

        Args:
            **options: Playwright screenshot options (path, full_page, etc.)

        Returns:
            Screenshot as bytes
        """
        options_str = ", ".join(f"{k}={v}" for k, v in options.items()) if options else "default"
        self._log_action(
            action="SCREENSHOT",
            details=f"Options: {options_str}"
        )
        return self._page.screenshot(**options)

    def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in page context

        Args:
            script: JavaScript code to execute

        Returns:
            Result of JavaScript execution
        """
        # Truncate long scripts in logs
        script_preview = script[:100] + "..." if len(script) > 100 else script
        self._log_action(
            action="EXECUTE_JAVASCRIPT",
            details=f"Script: {script_preview}"
        )
        result = self._page.evaluate(script)

        # Log result type
        self._log_action(
            action="JAVASCRIPT_RESULT",
            details=f"Type: {type(result).__name__}"
        )
        return result

    def on(self, event: str, handler: callable) -> None:
        """
        Add event listener

        Args:
            event: Event name (e.g., 'console', 'request', 'response')
            handler: Callback function for event

        Note:
            This method is not logged to avoid noise in logs
        """
        self._page.on(event, handler)

    def close(self) -> None:
        """Close page and cleanup resources"""
        self._log_action(
            action="CLOSE_PAGE",
            details="Closing page and releasing resources"
        )
        self._page.close()

    # Expose underlying Playwright page for advanced usage
    @property
    def playwright_page(self) -> Page:
        """Get underlying Playwright page (for advanced usage only)"""
        return self._page


class PlaywrightBrowserAdapter(IBrowser):
    """
    Adapter: Wraps Playwright Browser to implement IBrowser interface
    """

    def __init__(
        self,
        playwright_browser: Browser,
        sensitive_patterns: Optional[List[str]] = None,
        mask_character: str = "***"
    ):
        """
        Initialize adapter

        Args:
            playwright_browser: Actual Playwright Browser instance
            sensitive_patterns: Patterns for sensitive data masking (passed to pages)
            mask_character: Character/string for masking sensitive data
        """
        self._browser = playwright_browser
        self._context: Optional[BrowserContext] = None
        self._sensitive_patterns = sensitive_patterns
        self._mask_character = mask_character

    def new_page(self) -> IPage:
        """
        Create new page/tab with configured sensitive data masking

        Returns:
            IPage instance with enhanced action logging
        """
        if not self._context:
            self._context = self._browser.new_context()

        playwright_page = self._context.new_page()
        return PlaywrightPageAdapter(
            playwright_page,
            sensitive_patterns=self._sensitive_patterns,
            mask_character=self._mask_character
        )

    def close(self) -> None:
        """Close browser"""
        if self._context:
            self._context.close()
        self._browser.close()

    def contexts(self) -> List[Any]:
        """Get browser contexts"""
        return self._browser.contexts

    @property
    def playwright_browser(self) -> Browser:
        """Get underlying Playwright browser"""
        return self._browser

    @property
    def playwright_context(self) -> Optional[BrowserContext]:
        """Get underlying Playwright context"""
        return self._context


class PlaywrightBrowserDriver(IBrowserDriver):
    """
    Adapter: Playwright implementation of IBrowserDriver

    This is the main adapter that allows Clean Architecture.
    Domain/Application code depends on IBrowserDriver interface,
    not on this concrete Playwright implementation.

    Benefits:
    - Can swap Playwright for Selenium without changing domain code
    - Domain tests don't need Playwright
    - Framework independence
    """

    def __init__(
        self,
        sensitive_patterns: Optional[List[str]] = None,
        mask_character: str = "***"
    ):
        """
        Initialize Playwright driver

        Args:
            sensitive_patterns: Patterns for sensitive data masking in action logs
            mask_character: Character/string for masking sensitive data
        """
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browser_type: str = "chromium"
        self._sensitive_patterns = sensitive_patterns
        self._mask_character = mask_character

    def launch(
        self,
        headless: bool = False,
        args: Optional[List[str]] = None,
        **options
    ) -> IBrowser:
        """
        Launch browser with enhanced action logging configuration

        Args:
            headless: Run in headless mode
            args: Browser launch arguments
            **options: Additional Playwright-specific options

        Returns:
            IBrowser instance with configured action logging
        """
        # Start Playwright
        if not self._playwright:
            self._playwright = sync_playwright().start()

        # Get browser type
        browser_type = getattr(self._playwright, self._browser_type)

        # Launch browser
        self._browser = browser_type.launch(
            headless=headless,
            args=args or [],
            **options
        )

        # Return wrapped browser with sensitive data masking configuration
        return PlaywrightBrowserAdapter(
            self._browser,
            sensitive_patterns=self._sensitive_patterns,
            mask_character=self._mask_character
        )

    def close(self) -> None:
        """Close browser and cleanup resources"""
        if self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def is_running(self) -> bool:
        """Check if browser is currently running"""
        return self._browser is not None and self._browser.is_connected()

    def get_browser_type(self) -> str:
        """Get browser type (chromium, firefox, webkit)"""
        return self._browser_type

    def set_browser_type(self, browser_type: str) -> None:
        """
        Set browser type before launch

        Args:
            browser_type: chromium, firefox, or webkit
        """
        if browser_type not in ["chromium", "firefox", "webkit"]:
            raise ValueError(f"Invalid browser type: {browser_type}")
        self._browser_type = browser_type

    def create_context(
        self,
        browser: IBrowser,
        record_video: bool = False,
        record_har: bool = False,
        **options
    ) -> Any:
        """
        Create browser context with optional recording

        Args:
            browser: Browser instance (must be PlaywrightBrowserAdapter)
            record_video: Enable video recording
            record_har: Enable HAR recording
            **options: Additional context options

        Returns:
            Browser context
        """
        if not isinstance(browser, PlaywrightBrowserAdapter):
            raise TypeError("Browser must be PlaywrightBrowserAdapter")

        context_options = {**options}

        if record_video:
            context_options["record_video_dir"] = "videos/"

        if record_har:
            context_options["record_har_path"] = "network.har"

        return browser.playwright_browser.new_context(**context_options)

    def save_trace(self, trace_path: Path) -> None:
        """Save trace file from browser context."""
        if not self._browser:
            raise RuntimeError("Browser not running, cannot save trace")

        trace_path = Path(trace_path)
        trace_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all contexts and save traces
        for context in self._browser.contexts:
            try:
                # Stop tracing and save
                context.tracing.stop(path=str(trace_path))
            except Exception:
                # Tracing may not be enabled, ignore
                pass

    def save_video(self, video_path: Path) -> Optional[Path]:
        """Save video file from browser pages."""
        if not self._browser:
            return None

        video_path = Path(video_path)
        video_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all contexts and save videos from pages
        for context in self._browser.contexts:
            for page in context.pages:
                try:
                    video = page.video
                    if video:
                        # Close page to finalize video
                        page.close()
                        # Move video to desired path
                        actual_path = video.path()
                        if actual_path:
                            import shutil
                            shutil.move(actual_path, str(video_path))
                            return video_path
                except Exception:
                    # Video recording may not be enabled
                    pass

        return None

    def capture_screenshot(self) -> Optional[bytes]:
        """Capture screenshot from current active page."""
        if not self._browser:
            return None

        try:
            # Get all contexts and capture from first available page
            for context in self._browser.contexts:
                for page in context.pages:
                    return page.screenshot()
        except Exception:
            # Screenshot capture may fail
            pass

        return None

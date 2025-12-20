"""Playwright Adapter - Implementation of IBrowserDriver

This adapter wraps Playwright to implement the domain's IBrowserDriver interface.
This allows the domain to be independent of Playwright.
"""

from typing import Optional, List, Any, Callable
from pathlib import Path
import inspect

from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
)

from nemesis.domain.ports import IBrowserDriver, IBrowser, IPage
from nemesis.infrastructure.logging import Logger


class PlaywrightPageAdapter(IPage):
    """
    Adapter: Wraps Playwright Page to implement IPage interface

    This allows domain/application code to use IPage without knowing about Playwright.
    """

    def __init__(self, playwright_page: Page):
        """
        Initialize adapter with Playwright page

        Args:
            playwright_page: Actual Playwright Page instance
        """
        self._page = playwright_page
        self._logger = Logger.get_instance({})
        self._action_logger: Optional[Callable[[str], None]] = None

    def set_action_logger(self, logger_callback: Callable[[str], None]) -> None:
        """
        Set callback for logging actions to ReportPortal

        Args:
            logger_callback: Function that takes action message and logs it
        """
        self._action_logger = logger_callback

    def _log_action(self, action: str, details: str = "") -> None:
        """Log action with details"""
        try:
            message = f"[ACTION] {action}"
            if details:
                message += f" - {details}"

            # Log to local logger
            self._logger.info(f"[ACTION LOG] {message}")

            # Log to ReportPortal if callback is set
            if self._action_logger:
                self._logger.info(f"[ACTION RP] Calling action logger for: {message}")
                self._action_logger(message)
                self._logger.info(f"[ACTION RP] Action logger called for: {message}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Don't let logging failures break tests
            self._logger.warning(f"Failed to log action: {e}")

    def goto(self, url: str, **options) -> None:
        """Navigate to URL"""
        self._log_action("Navigate", f"URL: {url}")
        self._page.goto(url, **options)

    def click(self, selector: str, **options) -> None:
        """Click element"""
        self._log_action("Click", f"Selector: {selector}")
        self._page.click(selector, **options)

    def fill(self, selector: str, value: str, **options) -> None:
        """Fill input field"""
        # Show actual values in logs for better debugging
        self._log_action("Fill", f"Selector: {selector}, Value: {value}")
        self._page.fill(selector, value, **options)

    def get_text(self, selector: str) -> str:
        """Get element text content"""
        self._log_action("Get Text", f"Selector: {selector}")
        result = self._page.text_content(selector) or ""
        self._log_action("Text Retrieved", f"Length: {len(result)} chars")
        return result

    def is_visible(self, selector: str) -> bool:
        """Check if element is visible"""
        self._log_action("Check Visibility", f"Selector: {selector}")
        result = self._page.is_visible(selector)
        self._log_action("Visibility Check", f"Visible: {result}")
        return result

    def screenshot(self, **options) -> bytes:
        """Take screenshot"""
        self._log_action("Take Screenshot", f"Options: {list(options.keys()) if options else 'default'}")
        return self._page.screenshot(**options)

    def evaluate(self, script: str) -> Any:
        """Execute JavaScript"""
        # Truncate long scripts in logs
        script_preview = script[:50] + "..." if len(script) > 50 else script
        self._log_action("Execute JavaScript", f"Script: {script_preview}")
        result = self._page.evaluate(script)
        self._log_action("JavaScript Result", f"Type: {type(result).__name__}")
        return result

    def on(self, event: str, handler: callable) -> None:
        """Add event listener"""
        self._page.on(event, handler)

    def close(self) -> None:
        """Close page"""
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

    def __init__(self, playwright_browser: Browser):
        """
        Initialize adapter

        Args:
            playwright_browser: Actual Playwright Browser instance
        """
        self._browser = playwright_browser
        self._context: Optional[BrowserContext] = None

    def new_page(self) -> IPage:
        """Create new page/tab"""
        if not self._context:
            self._context = self._browser.new_context()

        playwright_page = self._context.new_page()
        return PlaywrightPageAdapter(playwright_page)

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

    def __init__(self):
        """Initialize Playwright driver"""
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browser_type: str = "chromium"

    def launch(
        self,
        headless: bool = False,
        args: Optional[List[str]] = None,
        **options
    ) -> IBrowser:
        """
        Launch browser

        Args:
            headless: Run in headless mode
            args: Browser launch arguments
            **options: Additional Playwright-specific options

        Returns:
            IBrowser instance (wrapped Playwright browser)
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

        # Return wrapped browser (implements IBrowser)
        return PlaywrightBrowserAdapter(self._browser)

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

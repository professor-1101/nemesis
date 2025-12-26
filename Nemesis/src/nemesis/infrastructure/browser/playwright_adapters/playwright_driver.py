"""Playwright Browser Driver - Implementation of IBrowserDriver interface.

Responsibilities:
- Launch and manage Playwright browser lifecycle
- Configure browser type (chromium, firefox, webkit)
- Create browser contexts with recording options
- Save traces, videos, and screenshots
"""
from typing import Any, List, Optional
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
)

from nemesis.domain.ports import IBrowserDriver, IBrowser
from .playwright_browser_adapter import PlaywrightBrowserAdapter


class PlaywrightBrowserDriver(IBrowserDriver):
    """
    Adapter: Playwright implementation of IBrowserDriver.

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
        Initialize Playwright driver.

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
        Launch browser with enhanced action logging configuration.

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
        """Close browser and cleanup resources."""
        if self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def is_running(self) -> bool:
        """Check if browser is currently running."""
        return self._browser is not None and self._browser.is_connected()

    def get_browser_type(self) -> str:
        """Get browser type (chromium, firefox, webkit)."""
        return self._browser_type

    def set_browser_type(self, browser_type: str) -> None:
        """
        Set browser type before launch.

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
        Create browser context with optional recording.

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

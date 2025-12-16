"""Browser Driver Port - Interface for browser automation

This interface allows swapping browser automation frameworks
(Playwright, Selenium, Puppeteer) without changing core logic.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol, Any, Optional, Dict, List
from pathlib import Path


class IPage(Protocol):
    """
    Interface for browser page

    Abstraction over Playwright.Page, Selenium.WebDriver, etc.
    """

    @abstractmethod
    def goto(self, url: str, **options) -> None:
        """Navigate to URL"""
        ...

    @abstractmethod
    def click(self, selector: str, **options) -> None:
        """Click element"""
        ...

    @abstractmethod
    def fill(self, selector: str, value: str, **options) -> None:
        """Fill input field"""
        ...

    @abstractmethod
    def get_text(self, selector: str) -> str:
        """Get element text content"""
        ...

    @abstractmethod
    def is_visible(self, selector: str) -> bool:
        """Check if element is visible"""
        ...

    @abstractmethod
    def screenshot(self, **options) -> bytes:
        """Take screenshot"""
        ...

    @abstractmethod
    def evaluate(self, script: str) -> Any:
        """Execute JavaScript"""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close page"""
        ...


class IBrowser(Protocol):
    """
    Interface for browser instance

    Abstraction over Playwright.Browser, Selenium browser, etc.
    """

    @abstractmethod
    def new_page(self) -> IPage:
        """Create new page/tab"""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close browser"""
        ...

    @abstractmethod
    def contexts(self) -> List[Any]:
        """Get browser contexts"""
        ...


class IBrowserDriver(ABC):
    """
    Port: Browser Driver Interface

    This is the main interface that infrastructure adapters must implement.
    It allows the core domain to be independent of specific browser automation frameworks.

    Implementations:
    - PlaywrightBrowserDriver (Infrastructure layer)
    - SeleniumBrowserDriver (future)
    - PuppeteerBrowserDriver (future)

    Clean Architecture: This interface lives in Domain layer.
    Implementations live in Infrastructure layer.
    """

    @abstractmethod
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
            **options: Additional browser options

        Returns:
            IBrowser instance
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close browser and cleanup resources"""
        ...

    @abstractmethod
    def is_running(self) -> bool:
        """Check if browser is currently running"""
        ...

    @abstractmethod
    def get_browser_type(self) -> str:
        """Get browser type (chromium, firefox, webkit)"""
        ...

    @abstractmethod
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
            browser: Browser instance
            record_video: Enable video recording
            record_har: Enable HAR recording
            **options: Additional context options

        Returns:
            Browser context
        """
        ...

    @abstractmethod
    def save_trace(self, trace_path: Path) -> None:
        """Save trace file"""
        ...

    @abstractmethod
    def save_video(self, video_path: Path) -> Optional[Path]:
        """Save video file"""
        ...

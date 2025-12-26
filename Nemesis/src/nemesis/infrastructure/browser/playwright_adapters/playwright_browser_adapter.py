"""Playwright Browser Adapter - Implementation of IBrowser interface.

Responsibilities:
- Adapt Playwright Browser to domain's IBrowser interface
- Create new pages with configured action logging
- Manage browser context
"""
from typing import Any, List, Optional
from playwright.sync_api import Browser, BrowserContext

from nemesis.domain.ports import IBrowser, IPage
from .playwright_page_adapter import PlaywrightPageAdapter


class PlaywrightBrowserAdapter(IBrowser):
    """
    Adapter: Wraps Playwright Browser to implement IBrowser interface.
    """

    def __init__(
        self,
        playwright_browser: Browser,
        sensitive_patterns: Optional[List[str]] = None,
        mask_character: str = "***"
    ):
        """
        Initialize adapter.

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
        Create new page/tab with configured sensitive data masking.

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
        """Close browser."""
        if self._context:
            self._context.close()
        self._browser.close()

    def contexts(self) -> List[Any]:
        """Get browser contexts."""
        return self._browser.contexts

    @property
    def playwright_browser(self) -> Browser:
        """Get underlying Playwright browser."""
        return self._browser

    @property
    def playwright_context(self) -> Optional[BrowserContext]:
        """Get underlying Playwright context."""
        return self._context

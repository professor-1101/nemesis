"""Base page object using Clean Architecture with IPage interface.

This refactored BasePage demonstrates:
- Using IPage interface instead of direct Playwright coupling
- Framework independence through abstraction
- Clean separation of concerns
"""

from typing import Any, Optional

# Use IPage interface from Domain layer
from nemesis.domain.ports import IPage


class BasePage:
    """
    Base page object for all pages using IPage interface.

    Clean Architecture:
    - Depends on IPage interface (Domain layer), not Playwright
    - Can work with any browser driver (Playwright, Selenium, etc.)
    - Framework-independent
    """

    def __init__(self, page: IPage, config: dict) -> None:
        """
        Initialize base page

        Args:
            page: IPage interface implementation (e.g., PlaywrightPageAdapter)
            config: Configuration dictionary
        """
        self.page = page
        self.config = config

        # Get base URL from config
        self.base_url = config.get("base_url", "https://www.saucedemo.com")

        # Access underlying Playwright page for advanced features
        # This is a pragmatic approach - for production, extend IPage interface
        if hasattr(page, 'playwright_page'):
            self._playwright_page = page.playwright_page
        else:
            self._playwright_page = None

    def navigate_to(self, path: str = "") -> None:
        """
        Navigate to URL

        Uses IPage.goto() - framework independent
        """
        url = f"{self.base_url}{path}"
        self.page.goto(url)

    def click(self, selector: str) -> None:
        """
        Click element

        Uses IPage.click() - framework independent
        """
        self.page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        """
        Fill input field

        Uses IPage.fill() - framework independent
        """
        self.page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """
        Get element text

        Uses IPage.get_text() - framework independent
        """
        return self.page.get_text(selector)

    def is_visible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Check if element is visible

        Uses IPage.is_visible() - framework independent
        """
        # IPage.is_visible() doesn't take timeout parameter
        # For production, extend IPage or use separate wait method
        return self.page.is_visible(selector)

    def wait_for_element(self, selector: str, timeout: int = 10000) -> None:
        """
        Wait for element to be visible

        Uses underlying Playwright page for advanced features
        For production: extend IPage interface or create separate waits abstraction
        """
        if self._playwright_page:
            try:
                self._playwright_page.wait_for_selector(selector, timeout=timeout)
            except Exception as e:
                raise TimeoutError(
                    f"Element not found within {timeout}ms: {selector}"
                ) from e
        else:
            # Fallback: just check visibility
            if not self.page.is_visible(selector):
                raise TimeoutError(f"Element not visible: {selector}")

    def assert_text_visible(self, text: str) -> None:
        """
        Assert text is visible on page

        Uses underlying Playwright page for advanced assertions
        For production: create separate assertions abstraction
        """
        if self._playwright_page:
            from playwright.sync_api import expect

            try:
                expect(self._playwright_page.locator(f"text={text}")).to_be_visible()
            except Exception as e:
                raise AssertionError(f"Text not visible: {text}") from e
        else:
            # Fallback: basic check
            raise NotImplementedError(
                "assert_text_visible requires Playwright page"
            )

    def assert_url_contains(self, expected: str) -> None:
        """
        Assert URL contains expected string

        Uses underlying Playwright page for URL access
        For production: add get_url() to IPage interface
        """
        if self._playwright_page:
            current_url = self._playwright_page.url
            if expected not in current_url:
                raise AssertionError(
                    f"URL does not contain '{expected}'. Current: {current_url}"
                )
        else:
            raise NotImplementedError("assert_url_contains requires Playwright page")

    def get_current_url(self) -> str:
        """
        Get current page URL

        Uses underlying Playwright page
        For production: add get_url() to IPage interface
        """
        if self._playwright_page:
            return self._playwright_page.url
        else:
            raise NotImplementedError("get_current_url requires Playwright page")

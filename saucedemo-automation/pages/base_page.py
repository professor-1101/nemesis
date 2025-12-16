"""Base page object with common functionality using sync Playwright API."""
from typing import Any

from playwright.sync_api import Page, expect

from nemesis.core.exceptions import ElementNotFoundError, TimeoutError
from nemesis.core.logging import Logger
from nemesis.utils.decorators import retry


class BasePage:
    """Base page object for all pages using sync Playwright API."""

    def __init__(self, page: Page, config: Any) -> None:
        self.page = page
        self.config = config
        self.logger = Logger.get_instance({})
        try:
            if hasattr(config, 'get'):
                self.base_url = config.get("env.base_url", "https://www.saucedemo.com")
            else:
                self.base_url = "https://www.saucedemo.com"
        except Exception:
            self.base_url = "https://www.saucedemo.com"

    def navigate_to(self, path: str = "") -> None:
        """Navigate to URL synchronously."""
        url = f"{self.base_url}{path}"
        self.logger.info(f"Navigating to: {url}")
        self.page.goto(url)

    @retry(max_attempts=3, delay=1.0)
    def click(self, selector: str) -> None:
        """Click element with retry synchronously."""
        try:
            self.page.click(selector)
            self.logger.debug(f"Clicked: {selector}")
        except Exception as e:
            raise ElementNotFoundError(f"Failed to click: {selector}", str(e))

    @retry(max_attempts=3, delay=1.0)
    def fill(self, selector: str, value: str) -> None:
        """Fill input field synchronously."""
        try:
            self.page.fill(selector, value)
            self.logger.debug(f"Filled: {selector}")
        except Exception as e:
            raise ElementNotFoundError(f"Failed to fill: {selector}", str(e))

    def get_text(self, selector: str) -> str:
        """Get element text synchronously."""
        try:
            return self.page.locator(selector).text_content() or ""
        except Exception as e:
            raise ElementNotFoundError(f"Failed to get text: {selector}", str(e))

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """Check if element is visible synchronously."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return self.page.locator(selector).is_visible()
        except Exception:
            return False

    def wait_for_element(self, selector: str, timeout: int = 10000) -> None:
        """Wait for element to be visible synchronously."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            raise TimeoutError(
                f"Element not found within {timeout}ms: {selector}", str(e)
            )

    def assert_text_visible(self, text: str) -> None:
        """Assert text is visible on page synchronously."""
        try:
            expect(self.page.locator(f"text={text}")).to_be_visible()
        except Exception as e:
            raise AssertionError(f"Text not visible: {text}", str(e))

    def assert_url_contains(self, expected: str) -> None:
        """Assert URL contains expected string synchronously."""
        current_url = self.page.url
        if expected not in current_url:
            raise AssertionError(
                f"URL does not contain '{expected}'. Current: {current_url}"
            )

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.page.url
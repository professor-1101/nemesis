"""Login page object using sync Playwright API."""
from typing import Any

from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Login page interactions using sync Playwright API."""

    # Selectors
    USERNAME_INPUT = "#user-name"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-button"
    ERROR_MESSAGE = "[data-test='error']"

    def __init__(self, page: Page, config: Any) -> None:
        super().__init__(page, config)

    def open(self) -> None:
        """Open login page synchronously."""
        self.navigate_to("/")

    def enter_username(self, username: str) -> None:
        """Enter username synchronously."""
        self.fill(self.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        """Enter password synchronously."""
        self.fill(self.PASSWORD_INPUT, password)

    def click_login_button(self) -> None:
        """Click login button synchronously."""
        self.click(self.LOGIN_BUTTON)
    
    def click_login(self) -> None:
        """Click login button synchronously (alias)."""
        self.click_login_button()

    def login(self, username: str, password: str) -> None:
        """Perform complete login synchronously."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()

    def get_error_message(self) -> str:
        """Get error message text synchronously."""
        return self.get_text(self.ERROR_MESSAGE)

    def is_error_visible(self) -> bool:
        """Check if error message is visible synchronously."""
        return self.is_visible(self.ERROR_MESSAGE)

    def is_on_login_page(self) -> bool:
        """Verify user is on login page synchronously."""
        return self.is_visible(self.LOGIN_BUTTON)
    
    def verify_page_loaded(self) -> None:
        """Verify login page is loaded synchronously."""
        if not self.is_on_login_page():
            raise Exception("Login page not loaded")
    
    def verify_error_message(self, expected_message: str) -> None:
        """Verify error message is displayed synchronously."""
        if not self.is_error_visible():
            raise Exception("Error message not visible")
        actual_message = self.get_error_message()
        if expected_message not in actual_message:
            raise Exception(f"Expected error message '{expected_message}' not found. Found: '{actual_message}'")
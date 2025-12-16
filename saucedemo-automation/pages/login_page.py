"""Login page object using Clean Architecture.

This refactored LoginPage demonstrates:
- Using IPage interface through BasePage
- Framework independence
- Clean separation of concerns
"""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


class LoginPage(BasePage):
    """
    Login page interactions using IPage interface.

    Clean Architecture:
    - Depends on IPage interface, not Playwright
    - Framework-independent
    - Business logic in page object
    """

    # Selectors
    USERNAME_INPUT = "#user-name"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "#login-button"
    ERROR_MESSAGE = "[data-test='error']"

    def __init__(self, page: IPage, config: dict) -> None:
        """
        Initialize login page

        Args:
            page: IPage interface implementation
            config: Configuration dictionary
        """
        super().__init__(page, config)

    def open(self) -> None:
        """Open login page"""
        self.navigate_to("/")

    def enter_username(self, username: str) -> None:
        """Enter username"""
        self.fill(self.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        """Enter password"""
        self.fill(self.PASSWORD_INPUT, password)

    def click_login_button(self) -> None:
        """Click login button"""
        self.click(self.LOGIN_BUTTON)

    def click_login(self) -> None:
        """Click login button (alias)"""
        self.click_login_button()

    def login(self, username: str, password: str) -> None:
        """
        Perform complete login flow

        Business logic encapsulated in page object
        """
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()

    def get_error_message(self) -> str:
        """Get error message text"""
        return self.get_text(self.ERROR_MESSAGE)

    def is_error_visible(self) -> bool:
        """Check if error message is visible"""
        return self.is_visible(self.ERROR_MESSAGE)

    def is_on_login_page(self) -> bool:
        """Verify user is on login page"""
        return self.is_visible(self.LOGIN_BUTTON)

    def verify_page_loaded(self) -> None:
        """Verify login page is loaded"""
        if not self.is_on_login_page():
            raise AssertionError("Login page not loaded")

    def verify_error_message(self, expected_message: str) -> None:
        """Verify error message is displayed"""
        if not self.is_error_visible():
            raise AssertionError("Error message not visible")

        actual_message = self.get_error_message()
        if expected_message not in actual_message:
            raise AssertionError(
                f"Expected error message '{expected_message}' not found. "
                f"Found: '{actual_message}'"
            )

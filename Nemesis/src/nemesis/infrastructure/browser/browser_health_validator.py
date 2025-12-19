"""Browser health validation service.

Validates browser instance health and responsiveness through page checks
and JavaScript execution tests.
"""

from playwright.sync_api import Page


class BrowserHealthValidator:
    """Validates browser health by checking page existence and responsiveness."""

    @staticmethod
    def validate_page_exists(page: Page | None) -> None:
        """
        Validate that page instance exists.

        Args:
            page: Page instance to validate

        Raises:
            ValueError: If page is None
        """
        if page is None:
            raise ValueError("Page instance is None - browser not healthy")

    @staticmethod
    def validate_browser_responsive(page: Page) -> bool:
        """
        Validate browser is responsive by executing simple JavaScript.

        Args:
            page: Page instance to test

        Returns:
            True if browser is responsive, False otherwise

        Example:
            >>> validator = BrowserHealthValidator()
            >>> is_responsive = validator.validate_browser_responsive(page)
        """
        try:
            # Simple JS evaluation to check if browser is responsive
            result = page.evaluate("() => true")
            return result is True
        except Exception:
            # Any exception means browser is not responsive
            return False

    @staticmethod
    def check_health(page: Page | None, is_healthy_flag: bool) -> bool:
        """
        Comprehensive health check combining multiple validations.

        Args:
            page: Page instance to check
            is_healthy_flag: Current health status flag

        Returns:
            True if all health checks pass, False otherwise
        """
        if not is_healthy_flag:
            return False

        if page is None:
            return False

        return BrowserHealthValidator.validate_browser_responsive(page)

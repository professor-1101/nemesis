"""Browser health validation service.

This service handles health checking and validation of browser instances.
Following SRP: Single responsibility is to validate browser health.
"""

from playwright.sync_api import Page


class BrowserHealthValidator:
    """
    Validates browser health and responsiveness.

    Responsibilities (SRP):
    - Check if page exists
    - Validate browser is responsive
    - Execute simple JavaScript to verify functionality

    This class was extracted from BrowserLifecycle to follow SRP.
    """

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

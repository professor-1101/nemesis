"""Browser cleanup and resource management."""
import traceback

from playwright.sync_api import Browser, BrowserContext, Page, Playwright

from nemesis.infrastructure.logging import Logger


class BrowserCleanup:
    """Handles browser cleanup and resource management."""

    def __init__(self):
        """Initialize browser cleanup."""
        self.logger = Logger.get_instance({})

    def cleanup_resources(
        self,
        playwright: Playwright | None,
        browser: Browser | None,
        context: BrowserContext | None,
        _page: Page | None
    ) -> None:
        """Clean up browser resources."""
        errors = []

        try:
            if context:
                context.close()
                self.logger.debug("Browser context closed")
        except (RuntimeError, AttributeError) as e:
            # Playwright context close errors
            error_msg = f"Context close failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserCleanup", method="cleanup_resources")
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise

        try:
            if browser:
                browser.close()
                self.logger.debug("Browser closed")
        except (RuntimeError, AttributeError) as e:
            # Browser close errors
            error_msg = f"Browser close failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserCleanup", method="cleanup_resources")
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise

        try:
            if playwright:
                playwright.stop()
                self.logger.debug("Playwright stopped")
        except (RuntimeError, AttributeError) as e:
            # Playwright stop errors
            error_msg = f"Playwright stop failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserCleanup", method="cleanup_resources")
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise

        if errors:
            self.logger.warning(f"Cleanup warnings: {'; '.join(errors)}")
        else:
            self.logger.info("Browser closed successfully")

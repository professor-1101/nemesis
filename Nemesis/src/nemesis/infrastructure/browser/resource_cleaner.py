"""Resource cleanup service for browser instances.

Handles graceful shutdown of browser resources with retry logic and error aggregation.
Ensures HAR files and videos are finalized before closing browser contexts.
"""

import time
import traceback
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, Playwright

from nemesis.infrastructure.logging import Logger


# Cleanup timing and retry constants
HAR_FINALIZATION_DELAY = 0.5  # Seconds to wait for HAR file finalization
VIDEO_FINALIZATION_DELAY = 0.5  # Seconds to wait for video file finalization
BROWSER_CLOSE_RETRY_DELAY = 0.2  # Seconds between browser close retries
MAX_BROWSER_CLOSE_RETRIES = 3


class ResourceCleaner:
    """
    Manages graceful shutdown of Playwright browser resources.

    Cleans up collectors, closes browser contexts with HAR finalization delay,
    closes browser with retry mechanism, and stops Playwright. Aggregates all
    cleanup errors instead of throwing exceptions to ensure complete shutdown.
    """

    def __init__(self, logger: Logger | None = None):
        """
        Initialize resource cleaner.

        Args:
            logger: Logger instance for logging (optional, creates if not provided)
        """
        self.logger = logger or Logger.get_instance({})

    def cleanup_all(
        self,
        browser: Browser | None,
        context: BrowserContext | None,
        playwright: Playwright | None,
        page: Page | None,
        collectors: dict[str, Any] | None = None
    ) -> list[str]:
        """
        Clean up all browser resources with comprehensive error handling.

        Args:
            browser: Browser instance to close
            context: Browser context to close
            playwright: Playwright instance to stop
            page: Page instance (for reference, not closed separately)
            collectors: Dictionary of collectors to dispose

        Returns:
            List of error messages encountered during cleanup
        """
        errors = []

        # Dispose collectors first
        if collectors:
            collector_errors = self.dispose_collectors(collectors)
            errors.extend(collector_errors)

        # Close context (HAR-safe)
        context_errors = self.close_context_safe(context)
        errors.extend(context_errors)

        # Close browser with retries
        browser_errors = self.close_browser_with_retries(browser)
        errors.extend(browser_errors)

        # Stop Playwright
        playwright_errors = self.stop_playwright(playwright)
        errors.extend(playwright_errors)

        # Log summary
        if errors:
            self.logger.warning(f"Cleanup warnings: {'; '.join(errors)}")
        else:
            self.logger.info("Browser closed successfully")

        return errors

    def dispose_collectors(self, collectors: dict[str, Any]) -> list[str]:
        """
        Dispose collectors to prevent late events during shutdown.

        Args:
            collectors: Dictionary of collector instances

        Returns:
            List of error messages
        """
        errors = []

        try:
            console_collector = collectors.get('console')
            network_collector = collectors.get('network')
            performance_collector = collectors.get('performance')

            if console_collector and hasattr(console_collector, "dispose"):
                console_collector.dispose()
            if network_collector and hasattr(network_collector, "dispose"):
                network_collector.dispose()
            # Performance collector is pull-based; no listeners to detach

            self.logger.debug("Collectors disposed and cleared")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (AttributeError, RuntimeError) as e:
            error_msg = f"Collector cleanup failed: {e}"
            errors.append(error_msg)
            self.logger.debug(
                error_msg,
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="ResourceCleaner",
                method="dispose_collectors"
            )

        return errors

    def close_context_safe(self, context: BrowserContext | None) -> list[str]:
        """
        Close browser context safely with HAR finalization delay.

        Args:
            context: Browser context to close

        Returns:
            List of error messages
        """
        errors = []

        try:
            if context:
                # Wait for HAR to finish writing before closing context
                time.sleep(HAR_FINALIZATION_DELAY)
                context.close()
                self.logger.debug("Browser context closed safely")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (RuntimeError, AttributeError) as e:
            error_msg = f"Context close failed: {e}"
            errors.append(error_msg)
            self.logger.debug(
                error_msg,
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="ResourceCleaner",
                method="close_context_safe"
            )

        return errors

    def close_browser_with_retries(
        self,
        browser: Browser | None,
        max_retries: int = MAX_BROWSER_CLOSE_RETRIES
    ) -> list[str]:
        """
        Close browser with retry mechanism.

        Args:
            browser: Browser instance to close
            max_retries: Maximum number of retry attempts

        Returns:
            List of error messages
        """
        errors = []

        try:
            if browser:
                # Retry browser close if it fails
                for attempt in range(max_retries):
                    try:
                        browser.close()
                        self.logger.debug("Browser closed successfully")
                        break
                    except (RuntimeError, AttributeError) as e:
                        if attempt == max_retries - 1:
                            raise e
                        time.sleep(BROWSER_CLOSE_RETRY_DELAY)

        except (KeyboardInterrupt, SystemExit):
            raise
        except (RuntimeError, AttributeError) as e:
            error_msg = f"Browser close failed after {max_retries} retries: {e}"
            errors.append(error_msg)
            self.logger.debug(
                error_msg,
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="ResourceCleaner",
                method="close_browser_with_retries"
            )

        return errors

    def stop_playwright(self, playwright: Playwright | None) -> list[str]:
        """
        Stop Playwright instance with error handling.

        Args:
            playwright: Playwright instance to stop

        Returns:
            List of error messages
        """
        errors = []

        try:
            if playwright:
                playwright.stop()
                self.logger.debug("Playwright stopped")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (RuntimeError, AttributeError) as e:
            error_msg = f"Playwright stop failed: {e}"
            errors.append(error_msg)
            self.logger.debug(
                error_msg,
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="ResourceCleaner",
                method="stop_playwright"
            )

        return errors

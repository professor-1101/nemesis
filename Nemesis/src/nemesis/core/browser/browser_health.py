"""Browser health monitoring."""
import traceback

from nemesis.core.exceptions.browser_exceptions import BrowserError
from nemesis.core.logging import Logger


class BrowserHealthMonitor:
    """Monitors browser health and validates operations."""

    def __init__(self):
        """Initialize health monitor."""
        self.logger = Logger.get_instance({})

    def validate_browser_health(self, page) -> None:
        """Validate browser is responsive."""
        if not page:
            raise BrowserError("Browser health check failed", "Page is None")

        try:
            # Simple health check - evaluate JavaScript
            result = page.evaluate("() => true")
            if result is not True:
                raise BrowserError(
                    "Browser health check failed",
                    "JavaScript evaluation returned unexpected result"
                )
        except (RuntimeError, AttributeError) as e:
            # Page.evaluate errors
            self.logger.error(f"Browser health check failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserHealthMonitor", method="validate_browser_health")
            raise BrowserError("Browser health check failed", str(e)) from e
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise

"""Main browser manager - REFACTORED."""

from nemesis.core.config import ConfigLoader
from nemesis.core.browser.browser_lifecycle import BrowserLifecycle
from nemesis.core.browser.browser_launcher import BrowserLauncher
from nemesis.core.browser.browser_cleanup import BrowserCleanup
from nemesis.core.browser.browser_health import BrowserHealthMonitor


class BrowserManager:
    """Main browser manager that orchestrates all browser components."""

    def __init__(self, config: ConfigLoader) -> None:
        """Initialize browser manager.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.lifecycle = BrowserLifecycle(config)
        self.launcher = BrowserLauncher(config)
        self.cleanup = BrowserCleanup()
        self.health_monitor = BrowserHealthMonitor()

    def start(self, execution_id: str):
        """Start browser and create page."""
        return self.lifecycle.start(execution_id)

    def close(self) -> None:
        """Close browser and cleanup resources."""
        self.lifecycle.close()

    def stop(self) -> None:
        """Stop browser (alias for close)."""
        self.lifecycle.close()

    def managed_browser(self, execution_id: str):
        """Context manager for safe browser lifecycle."""
        return self.lifecycle.managed_browser(execution_id)

    @property
    def is_healthy(self) -> bool:
        """Check if browser is healthy and ready."""
        return self.lifecycle.is_healthy

    def get_page(self):
        """Get current page instance."""
        return self.lifecycle.get_page()

    def get_browser(self):
        """Get current browser instance."""
        return self.lifecycle.get_browser()

    # Backward compatibility methods
    def _get_browser_type(self) -> str:
        """Get browser type from config."""
        return self.launcher.get_browser_type()

    def _get_browser_args(self) -> list[str]:
        """Get browser launch arguments."""
        return self.launcher.get_browser_args()

    def _get_viewport(self) -> dict[str, int]:
        """Get viewport configuration."""
        return self.launcher.get_viewport()

    def _build_context_options(self, execution_id: str) -> dict[str, any]:
        """Build context creation options."""
        return self.launcher.build_context_options(execution_id)

    def _cleanup_resources(self) -> None:
        """Internal cleanup without lock."""
        self.cleanup.cleanup_resources(
            self.lifecycle._playwright,
            self.lifecycle._browser,
            self.lifecycle._context,
            self.lifecycle._page
        )

    @property
    def _context(self):
        """Get browser context for backward compatibility."""
        return self.lifecycle._context

    @_context.setter
    def _context(self, value):
        """Set browser context for backward compatibility."""
        self.lifecycle._context = value

    # Add missing properties for backward compatibility
    @property
    def _browser(self):
        """Get browser instance for backward compatibility."""
        return self.lifecycle._browser

    @property
    def _page(self):
        """Get page instance for backward compatibility."""
        return self.lifecycle._page

    @property
    def _playwright(self):
        """Get playwright instance for backward compatibility."""
        return self.lifecycle._playwright

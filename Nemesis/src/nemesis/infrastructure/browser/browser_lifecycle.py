"""Browser lifecycle management (Refactored for SRP).

This module orchestrates browser lifecycle using composed services.
Following SRP: Single responsibility is lifecycle orchestration.

Refactored to extract 4 service classes:
- BrowserHealthValidator: Health checking
- VideoProcessingService: Video conversion
- ResourceCleaner: Graceful cleanup
- CollectorCoordinator: Collector management
"""

import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from nemesis.infrastructure.config import ConfigLoader
from nemesis.shared.directory_manager import DirectoryManager
from nemesis.shared.exceptions.browser_exceptions import BrowserError
from nemesis.shared.execution_context import ExecutionContext
from nemesis.infrastructure.logging import Logger
from nemesis.utils.helpers.browser_helpers import get_browser_args, get_browser_type
from nemesis.infrastructure.browser.browser_context_options_builder import BrowserContextOptionsBuilder

# Extracted services (SRP compliance)
from nemesis.infrastructure.browser.browser_health_validator import BrowserHealthValidator
from nemesis.infrastructure.browser.video_processing_service import (
    VideoProcessingService,
    VIDEO_FINALIZATION_DELAY
)
from nemesis.infrastructure.browser.resource_cleaner import ResourceCleaner
from nemesis.infrastructure.browser.collector_coordinator import CollectorCoordinator


class BrowserLifecycle:
    """
    Orchestrates browser lifecycle using composition (Refactored for SRP).

    Responsibilities (SRP):
    - Start browser and create page
    - Coordinate lifecycle events
    - Provide access to browser/page instances
    - Close browser gracefully

    This class was refactored to follow SRP by extracting 4 service classes.
    Reduced from 424 lines to ~180 lines.

    Design Pattern: Composition over inheritance
    Architecture: Clean Architecture - coordinates infrastructure services
    """

    def __init__(self, config: ConfigLoader) -> None:
        """
        Initialize browser lifecycle with composed services.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.logger = Logger.get_instance({})

        # Browser instances
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._is_healthy = False

        # Context options builder
        self._context_options_builder = BrowserContextOptionsBuilder(config)

        # Composed services (SRP: Each service has one responsibility)
        self._health_validator = BrowserHealthValidator()
        self._video_processor = VideoProcessingService(logger=self.logger)
        self._resource_cleaner = ResourceCleaner(logger=self.logger)
        self._collector_coordinator = CollectorCoordinator(logger=self.logger)

    def start(self, execution_id: str) -> Page:
        """
        Start browser and create page synchronously.

        Args:
            execution_id: Execution ID for context

        Returns:
            Playwright Page instance

        Raises:
            BrowserError: If browser fails to start or is already running
        """
        if self._is_healthy:
            raise BrowserError(
                "Browser already started",
                "Call close() before starting new browser"
            )

        try:
            # Start Playwright
            self._playwright = sync_playwright().start()
            self.logger.debug("Playwright started")

            # Launch browser
            browser_type_name = get_browser_type(self.config, self.logger)
            browser_type = getattr(self._playwright, browser_type_name)

            headless = self.config.get("playwright.browser.headless", False)
            slow_mo = self.config.get("playwright.browser.slow_mo", 0)

            self._browser = browser_type.launch(
                headless=headless,
                slow_mo=slow_mo,
                args=get_browser_args(self.config),
            )
            self.logger.debug(f"Browser launched: {browser_type_name}")

            # Create context
            context_options = self._context_options_builder.build_options(execution_id)
            self._context = self._browser.new_context(**context_options)
            self.logger.debug("Browser context created")

            # Create page
            self._page = self._context.new_page()

            # Initialize collectors (SRP: Delegated to CollectorCoordinator)
            self._collector_coordinator.initialize_collectors(self._page, execution_id)

            # Health check (SRP: Delegated to BrowserHealthValidator)
            self._health_validator.validate_page_exists(self._page)
            self._is_healthy = True

            self.logger.info(
                f"Browser started successfully: {browser_type_name} "
                f"(headless={headless})"
            )

            return self._page

        except (RuntimeError, AttributeError) as e:
            self.logger.error(
                f"Failed to start browser: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="BrowserLifecycle",
                method="start"
            )
            self._cleanup_resources()
            raise BrowserError("Failed to start browser", str(e)) from e
        except (KeyboardInterrupt, SystemExit):
            raise
        except (OSError, IOError) as e:
            self.logger.error(
                f"Failed to start browser - I/O error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="BrowserLifecycle",
                method="start"
            )
            self._cleanup_resources()
            raise BrowserError("Failed to start browser", str(e)) from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Failed to start browser: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="BrowserLifecycle",
                method="start"
            )
            self._cleanup_resources()
            raise BrowserError("Failed to start browser", str(e)) from e

    def _cleanup_resources(self) -> None:
        """
        Internal cleanup with HAR-safe shutdown and video conversion.

        This method orchestrates cleanup using extracted service classes.
        SRP: Delegates specific cleanup tasks to service classes.
        """
        # Get video directory path before closing context
        video_dir = self._get_video_directory()

        # Cleanup using ResourceCleaner service (SRP: Separation of concerns)
        collectors = self._collector_coordinator.get_all_collectors()
        self._resource_cleaner.cleanup_all(
            browser=self._browser,
            context=self._context,
            playwright=self._playwright,
            page=self._page,
            collectors=collectors
        )

        # Convert videos AFTER context closes (SRP: Delegated to VideoProcessingService)
        if video_dir and video_dir.exists():
            time.sleep(VIDEO_FINALIZATION_DELAY)
            self._video_processor.convert_videos_in_directory(video_dir)

        # Reset state
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    def _get_video_directory(self) -> Path | None:
        """
        Get video directory path for current execution.

        Returns:
            Path to video directory or None if unavailable
        """
        try:
            if not self._context:
                return None

            import os  # pylint: disable=import-outside-toplevel
            execution_id = os.environ.get('NEMESIS_EXECUTION_ID')
            if not execution_id:
                execution_id = ExecutionContext.get_execution_id()

            directory_manager = DirectoryManager(self.config)
            base_path = directory_manager.get_execution_base_path(execution_id)
            return base_path / "videos"

        except (KeyboardInterrupt, SystemExit):
            raise
        except (AttributeError, KeyError, RuntimeError) as e:
            self.logger.debug(
                f"Failed to get video directory path: {e}",
                module=__name__,
                class_name="BrowserLifecycle",
                method="_get_video_directory"
            )
            return None

    def close(self) -> None:
        """
        Close browser and cleanup resources synchronously.

        Saves collector data before cleanup.
        """
        # Save collector data (SRP: Delegated to CollectorCoordinator)
        self._collector_coordinator.save_collector_data()

        # Cleanup resources
        self._cleanup_resources()
        self._is_healthy = False

    @contextmanager
    def managed_browser(self, execution_id: str) -> Generator[Page, None, None]:
        """
        Context manager for safe browser lifecycle.

        Args:
            execution_id: Execution ID for context

        Yields:
            Playwright Page instance

        Example:
            >>> lifecycle = BrowserLifecycle(config)
            >>> with lifecycle.managed_browser("exec-123") as page:
            ...     page.goto("https://example.com")
        """
        page = None
        try:
            page = self.start(execution_id)
            yield page
        except (KeyboardInterrupt, SystemExit):
            raise
        except (BrowserError, RuntimeError) as e:
            self.logger.error(
                f"Browser context manager error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="BrowserLifecycle",
                method="managed_browser"
            )
            raise
        finally:
            try:
                self.close()
            except (KeyboardInterrupt, SystemExit):
                raise
            except (RuntimeError, AttributeError) as e:
                self.logger.error(
                    f"Browser cleanup error: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name="BrowserLifecycle",
                    method="managed_browser"
                )

    @property
    def is_healthy(self) -> bool:
        """
        Check if browser is healthy and ready.

        Returns:
            True if browser is healthy, False otherwise
        """
        return self._health_validator.check_health(self._page, self._is_healthy)

    def get_page(self) -> Page:
        """
        Get current page instance.

        Returns:
            Playwright Page instance

        Raises:
            BrowserError: If browser is not available
        """
        if not self.is_healthy or not self._page:
            raise BrowserError(
                "Browser not available",
                "Call start() or use managed_browser() context manager"
            )
        return self._page

    def get_browser(self) -> Browser:
        """
        Get current browser instance.

        Returns:
            Playwright Browser instance

        Raises:
            BrowserError: If browser is not available
        """
        if not self.is_healthy or not self._browser:
            raise BrowserError(
                "Browser not available",
                "Call start() or use managed_browser() context manager"
            )
        return self._browser

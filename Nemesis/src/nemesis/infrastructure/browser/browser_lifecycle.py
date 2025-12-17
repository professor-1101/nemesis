"""Browser lifecycle management."""

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
from nemesis.utils.helpers.browser_helpers import get_browser_args, get_browser_type, get_viewport
from nemesis.utils.helpers.har_helpers import add_har_path_to_options


class BrowserLifecycle:
    """Manages browser lifecycle operations."""

    def __init__(self, config: ConfigLoader) -> None:
        """Initialize browser lifecycle.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.logger = Logger.get_instance({})

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._is_healthy = False

        # Collectors
        self._console_collector = None
        self._network_collector = None
        self._performance_collector = None

    def start(self, execution_id: str) -> Page:
        """Start browser and create page synchronously."""
        if self._is_healthy:
            raise BrowserError(
                "Browser already started",
                "Call close() before starting new browser"
            )

        try:
            self._playwright = sync_playwright().start()
            self.logger.debug("Playwright started")

            browser_type_name = self._get_browser_type()
            browser_type = getattr(self._playwright, browser_type_name)

            headless = self.config.get("playwright.browser.headless", False)
            slow_mo = self.config.get("playwright.browser.slow_mo", 0)

            self._browser = browser_type.launch(
                headless=headless,
                slow_mo=slow_mo,
                args=self._get_browser_args(),
            )
            self.logger.debug(f"Browser launched: {browser_type_name}")

            context_options = self._build_context_options(execution_id)
            self._context = self._browser.new_context(**context_options)
            self.logger.debug("Browser context created")

            self._page = self._context.new_page()

            # Initialize collectors BEFORE marking healthy
            self._initialize_collectors(execution_id)

            # Health check - simple validation
            if not self._page:
                raise BrowserError("Page not created", "Failed to create page")

            self._is_healthy = True

            self.logger.info(
                f"Browser started successfully: {browser_type_name} "
                f"(headless={headless})"
            )

            return self._page

        except (RuntimeError, AttributeError) as e:
            # Playwright initialization or browser launch errors
            self.logger.error(f"Failed to start browser: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="start")
            # Cleanup on failure
            self._cleanup_resources()
            raise BrowserError("Failed to start browser", str(e)) from e
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (OSError, IOError) as e:
            # File system errors during browser setup
            self.logger.error(f"Failed to start browser - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="start")
            self._cleanup_resources()
            raise BrowserError("Failed to start browser", str(e)) from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from Playwright SDK
            # NOTE: Playwright SDK may raise various exceptions we cannot predict
            self.logger.error(f"Failed to start browser: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="start")
            # Cleanup on failure
            self._cleanup_resources()
            raise BrowserError("Failed to start browser", str(e)) from e

    def _get_browser_type(self) -> str:
        """Get browser type from config."""
        return get_browser_type(self.config, self.logger)

    def _get_browser_args(self) -> list[str]:
        """Get browser launch arguments."""
        return get_browser_args(self.config)

    def _get_viewport(self) -> dict[str, int]:
        """Get viewport configuration."""
        return get_viewport(self.config, self.logger)

    def _validate_browser_health(self) -> None:
        """Validate browser is responsive."""
        if not self._page:
            raise BrowserError("Browser health check failed", "Page is None")

        try:
            # Simple health check - evaluate JavaScript
            result = self._page.evaluate("() => true")
            if result is not True:
                raise BrowserError(
                    "Browser health check failed",
                    "JavaScript evaluation returned unexpected result"
                )
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (RuntimeError, AttributeError) as e:
            # Page.evaluate errors
            self.logger.error(f"Browser health check failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_validate_browser_health")
            raise BrowserError("Browser health check failed", str(e)) from e

    def _build_context_options(self, execution_id: str) -> dict[str, any]:
        """Build context creation options."""
        ignore_https_errors = self.config.get(
            "playwright.context.ignore_https_errors", True
        )

        options: dict[str, any] = {
            "viewport": self._get_viewport(),
            "ignore_https_errors": ignore_https_errors,
        }

        # Use DirectoryManager for centralized directory management
        directory_manager = DirectoryManager(self.config)

        # Video recording - check attachments config
        videos_enabled = directory_manager.should_create_directory("videos")

        if videos_enabled:
            # Get the videos directory path directly
            base_path = directory_manager.get_execution_base_path(execution_id)
            videos_dir = base_path / "videos"

            # Ensure videos directory exists
            videos_dir.mkdir(parents=True, exist_ok=True)

            options["record_video_dir"] = str(videos_dir)
            options["record_video_size"] = self._get_viewport()
            self.logger.debug(f"Video recording enabled: {videos_dir}")
        else:
            self.logger.debug("Video recording disabled in attachments config")

        # HAR recording - check attachments config with robust error handling
        add_har_path_to_options(options, directory_manager, execution_id, self.logger)
        # Add HAR-specific options for stability (using correct Playwright API) if HAR is enabled
        if "record_har_path" in options:
            options["record_har_mode"] = "full"  # Full HAR recording
            options["record_har_omit_content"] = False  # Include content
            # Note: record_har_include_responses is not a valid Playwright option
            # Note: record_har_timeout is not a valid Playwright option
            self.logger.debug(f"HAR recording enabled with valid options: {options.get('record_har_path')}")
        else:
            self.logger.debug("HAR recording disabled in attachments config")

        return options

    def _cleanup_resources(self) -> None:
        """Internal cleanup without lock with HAR-safe shutdown."""
        errors = []

        # Store video directory path before closing context
        video_dir = None
        try:
            if self._context:
                # Get video directory path before closing
                import os  # pylint: disable=import-outside-toplevel
                execution_id = os.environ.get('NEMESIS_EXECUTION_ID')
                if not execution_id:
                    execution_id = ExecutionContext.get_execution_id()

                directory_manager = DirectoryManager(self.config)
                base_path = directory_manager.get_execution_base_path(execution_id)
                video_dir = base_path / "videos"
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, KeyError, RuntimeError) as e:
            # DirectoryManager errors - continue without video conversion
            self.logger.debug(f"Failed to get video directory path: {e}", module=__name__, class_name="BrowserLifecycle", method="_cleanup_resources")

        # Dispose collectors first to prevent late events during shutdown
        try:
            if self._console_collector and hasattr(self._console_collector, "dispose"):
                self._console_collector.dispose()
            if self._network_collector and hasattr(self._network_collector, "dispose"):
                self._network_collector.dispose()
            # Performance collector is pull-based; no listeners to detach
            self._console_collector = None
            self._network_collector = None
            self._performance_collector = None
            self.logger.debug("Collectors disposed and cleared")
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Collector dispose errors - log but continue
            error_msg = f"Collector cleanup failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_cleanup_resources")

        # HAR-safe context closure with timeout
        try:
            if self._context:
                # Wait for HAR to finish writing before closing context
                time.sleep(0.5)  # Give HAR time to finalize
                self._context.close()
                self.logger.debug("Browser context closed safely")

                # Convert videos AFTER context closes (Playwright saves videos on context close)
                if video_dir and video_dir.exists():
                    time.sleep(0.5)  # Wait for Playwright to finish writing video
                    self._convert_videos_in_directory(video_dir)
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (RuntimeError, AttributeError) as e:
            # Playwright context close errors
            error_msg = f"Context close failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_cleanup_resources")

        # Browser closure with retry mechanism
        try:
            if self._browser:
                # Retry browser close if it fails
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self._browser.close()
                        self.logger.debug("Browser closed successfully")
                        break
                    except (RuntimeError, AttributeError) as e:
                        if attempt == max_retries - 1:
                            raise e
                        time.sleep(0.2)  # Wait before retry
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (RuntimeError, AttributeError) as e:
            # Browser close errors after retries
            error_msg = f"Browser close failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_cleanup_resources")

        # Playwright stop with error handling
        try:
            if self._playwright:
                self._playwright.stop()
                self.logger.debug("Playwright stopped")
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (RuntimeError, AttributeError) as e:
            # Playwright stop errors
            error_msg = f"Playwright stop failed: {e}"
            errors.append(error_msg)
            self.logger.debug(error_msg, traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_cleanup_resources")

        # Reset state
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

        if errors:
            self.logger.warning(f"Cleanup warnings: {'; '.join(errors)}")
        else:
            self.logger.info("Browser closed successfully with HAR support")

    def close(self) -> None:
        """Close browser and cleanup resources synchronously."""
        # Save collector data before cleanup
        self._save_collector_data()
        self._cleanup_resources()
        self._is_healthy = False

    @contextmanager
    def managed_browser(
        self, execution_id: str
    ) -> Generator[Page, None, None]:
        """Context manager for safe browser lifecycle."""
        page = None
        try:
            page = self.start(execution_id)
            yield page
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (BrowserError, RuntimeError) as e:
            # Browser start errors
            self.logger.error(f"Browser context manager error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="managed_browser")
            raise
        finally:
            try:
                self.close()
            except (KeyboardInterrupt, SystemExit):
                # Always re-raise these to allow proper program termination
                raise
            except (RuntimeError, AttributeError) as e:
                # Browser cleanup errors
                self.logger.error(f"Browser cleanup error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="managed_browser")

    def _initialize_collectors(self, _execution_id: str) -> None:
        """Initialize data collectors."""
        try:
            # Lazy import to avoid circular imports
            from nemesis.infrastructure.collectors.console import ConsoleCollector  # pylint: disable=import-outside-toplevel
            from nemesis.infrastructure.collectors.network import NetworkCollector  # pylint: disable=import-outside-toplevel
            from nemesis.infrastructure.collectors.performance import PerformanceCollector  # pylint: disable=import-outside-toplevel

            # Console collector
            self._console_collector = ConsoleCollector(
                page=self._page,
                filter_levels=["error", "warning", "info"]
            )

            # Network collector
            self._network_collector = NetworkCollector(
                page=self._page,
                capture_requests=True,
                capture_responses=True
            )

            # Performance collector
            self._performance_collector = PerformanceCollector(
                page=self._page,
                capture_metrics=True
            )

            self.logger.info("Collectors initialized successfully")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (ImportError, AttributeError, RuntimeError) as e:
            # Collector initialization errors - log but continue
            self.logger.warning(f"Failed to initialize collectors: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_initialize_collectors")

    def _convert_videos_in_directory(self, video_dir: Path) -> None:
        """
        Convert all webm videos in directory to MP4.

        This ensures videos are converted for BOTH local storage AND ReportPortal.
        Videos converted here will be in MP4 format when VideoManager.attach_video()
        is called (if it's called), or will be ready for direct RP upload.
        """
        try:
            if not video_dir.exists():
                return

            # Convert all .webm files to .mp4
            import subprocess  # pylint: disable=import-outside-toplevel
            from nemesis.utils.video_converter import convert_to_mp4  # pylint: disable=import-outside-toplevel

            webm_files = list(video_dir.glob("*.webm"))
            if not webm_files:
                return

            self.logger.info(f"Converting {len(webm_files)} video(s) to MP4 (for all reporters)...")
            for webm_file in webm_files:
                try:
                    mp4_file = convert_to_mp4(webm_file)
                    if mp4_file and mp4_file != webm_file:
                        self.logger.debug(f"Converted: {webm_file.name} -> {mp4_file.name}")
                except (KeyboardInterrupt, SystemExit):
                    # Always re-raise these to allow proper program termination
                    raise
                except (OSError, RuntimeError, subprocess.SubprocessError) as e:
                    # Video conversion errors for single file - continue with others
                    self.logger.warning(f"Failed to convert {webm_file.name}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_convert_videos_in_directory", video_file=str(webm_file))

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (OSError, ImportError) as e:
            # Video conversion setup errors
            self.logger.warning(f"Video conversion error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_convert_videos_in_directory")

    def _save_collector_data(self) -> None:
        """Save collector data to files."""
        try:
            import os  # pylint: disable=import-outside-toplevel
            execution_id = os.environ.get('NEMESIS_EXECUTION_ID')
            if not execution_id:
                execution_id = ExecutionContext.get_execution_id()

            # Save console logs
            if self._console_collector:
                self._console_collector.save_to_file(execution_id, "console")
                self.logger.info("Console logs saved")

            # Save network data
            if self._network_collector:
                self._network_collector.save_metrics(execution_id, "network_metric")
                self.logger.info("Network metrics saved")

            # Save performance data
            if self._performance_collector:
                self._performance_collector.save_to_file(execution_id, "performance_metric")
                self.logger.info("Performance metrics saved")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (OSError, IOError, AttributeError, RuntimeError) as e:
            # Collector data save errors - log but don't fail
            self.logger.warning(f"Failed to save collector data: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserLifecycle", method="_save_collector_data")

    @property
    def is_healthy(self) -> bool:
        """Check if browser is healthy and ready."""
        return self._is_healthy and self._page is not None

    def get_page(self) -> Page:
        """Get current page instance."""
        if not self.is_healthy or not self._page:
            raise BrowserError(
                "Browser not available",
                "Call start() or use managed_browser() context manager"
            )
        return self._page

    def get_browser(self):
        """Get current browser instance."""
        if not self.is_healthy or not self._browser:
            raise BrowserError(
                "Browser not available",
                "Call start() or use managed_browser() context manager"
            )
        return self._browser

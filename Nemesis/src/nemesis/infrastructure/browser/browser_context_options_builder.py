"""Browser context options builder service."""

from pathlib import Path
from typing import Any, Dict

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.shared.directory_service import DirectoryService
from nemesis.utils.helpers.browser_helpers import get_viewport
from nemesis.utils.helpers.har_helpers import add_har_path_to_options


class BrowserContextOptionsBuilder:
    """Builds browser context creation options with proper configuration."""

    def __init__(self, config: ConfigLoader) -> None:
        """Initialize browser context options builder.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.logger = Logger.get_instance({})
        self.directory_manager = DirectoryService(config)

    def build_options(self, execution_id: str) -> Dict[str, Any]:
        """Build complete context creation options.

        Args:
            execution_id: Execution ID for directory management

        Returns:
            Dictionary of context options for Playwright
        """
        options: Dict[str, Any] = {
            "viewport": self._get_viewport(),
            "ignore_https_errors": self._get_ignore_https_errors(),
        }

        self._add_video_recording_options(options, execution_id)
        self._add_har_recording_options(options, execution_id)

        return options

    def _get_viewport(self) -> Dict[str, int]:
        """Get viewport configuration.

        Returns:
            Viewport dimensions
        """
        return get_viewport(self.config, self.logger)

    def _get_ignore_https_errors(self) -> bool:
        """Get HTTPS error handling configuration.

        Returns:
            True to ignore HTTPS errors, False otherwise
        """
        return self.config.get(
            "playwright.context.ignore_https_errors", True
        )

    def _add_video_recording_options(
        self,
        options: Dict[str, Any],
        execution_id: str
    ) -> None:
        """Add video recording options to context.

        Args:
            options: Context options dictionary to modify
            execution_id: Execution ID for directory management
        """
        videos_enabled = self.directory_manager.should_create_directory("videos")

        if videos_enabled:
            # Get the videos directory path directly
            base_path = self.directory_manager.get_execution_base_path(execution_id)
            videos_dir = base_path / "videos"

            # Ensure videos directory exists
            videos_dir.mkdir(parents=True, exist_ok=True)

            options["record_video_dir"] = str(videos_dir)
            options["record_video_size"] = self._get_viewport()
            self.logger.debug(f"Video recording enabled: {videos_dir}")
        else:
            self.logger.debug("Video recording disabled in attachments config")

    def _add_har_recording_options(
        self,
        options: Dict[str, Any],
        execution_id: str
    ) -> None:
        """Add HAR recording options to context.

        Args:
            options: Context options dictionary to modify
            execution_id: Execution ID for directory management
        """
        # HAR recording - check attachments config with robust error handling
        add_har_path_to_options(options, self.directory_manager, execution_id, self.logger)

        # Add HAR-specific options for stability (using correct Playwright API) if HAR is enabled
        if "record_har_path" in options:
            options["record_har_mode"] = "full"  # Full HAR recording
            options["record_har_omit_content"] = False  # Include content
            # Note: record_har_include_responses is not a valid Playwright option
            # Note: record_har_timeout is not a valid Playwright option
            self.logger.debug(f"HAR recording enabled with valid options: {options.get('record_har_path')}")
        else:
            self.logger.debug("HAR recording disabled in attachments config")

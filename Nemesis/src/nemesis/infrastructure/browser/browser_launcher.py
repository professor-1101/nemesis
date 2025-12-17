"""Browser launching and configuration."""

from typing import Any

from nemesis.infrastructure.config import ConfigLoader
from nemesis.shared.directory_manager import DirectoryManager
from nemesis.infrastructure.logging import Logger
from nemesis.utils.helpers.browser_helpers import get_browser_args, get_browser_type, get_viewport
from nemesis.utils.helpers.har_helpers import add_har_path_to_options


class BrowserLauncher:
    """Handles browser launching and configuration."""

    def __init__(self, config: ConfigLoader):
        """Initialize browser launcher.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.logger = Logger.get_instance({})

    def get_browser_type(self) -> str:
        """Get browser type from config."""
        return get_browser_type(self.config, self.logger)

    def get_browser_args(self) -> list[str]:
        """Get browser launch arguments."""
        return get_browser_args(self.config)

    def get_viewport(self) -> dict[str, int]:
        """Get viewport configuration."""
        return get_viewport(self.config, self.logger)

    def build_context_options(self, execution_id: str) -> dict[str, Any]:
        """Build context creation options."""
        options: dict[str, Any] = {
            "viewport": self.get_viewport(),
            "ignore_https_errors": self.config.get(
                "playwright.context.ignore_https_errors", True
            ),
        }

        # Use DirectoryManager for centralized directory management
        directory_manager = DirectoryManager(self.config)

        # Video recording - check attachments config
        videos_enabled = directory_manager.should_create_directory("videos")

        if videos_enabled:
            video_path = directory_manager.get_attachment_path(execution_id, "videos", "")
            if video_path:
                options["record_video_dir"] = str(video_path.parent)
                options["record_video_size"] = self.get_viewport()
                self.logger.debug(f"Video recording enabled: {video_path.parent}")

        # HAR recording - check attachments config
        add_har_path_to_options(options, directory_manager, execution_id, self.logger)

        return options

"""Browser operations for trace, screenshots, and video."""
import traceback
from pathlib import Path

from playwright.sync_api import Page

from nemesis.infrastructure.logging import Logger


class BrowserOperations:
    """Handles browser trace, screenshot, and video operations."""

    def __init__(self, page: Page, execution_id: str) -> None:
        """Initialize browser operations."""
        self.page = page
        self.context = page.context
        self.execution_id = execution_id
        self.logger = Logger.get_instance({})

    def get_video_path(self) -> Path | None:
        """Get video path if recording is enabled."""
        try:
            video = self.page.video
            if video:
                return Path(video.path())
            return None
        except (RuntimeError, AttributeError) as e:
            # Playwright API errors - video path retrieval failed
            self.logger.error(f"Failed to get video path: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserOperations", method="get_video_path", execution_id=self.execution_id)
            return None
        except (OSError, IOError) as e:
            # File path errors
            self.logger.error(f"Failed to get video path - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserOperations", method="get_video_path", execution_id=self.execution_id)
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from Playwright video API
            # NOTE: Playwright video API may raise various exceptions we cannot predict
            self.logger.error(f"Failed to get video path: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserOperations", method="get_video_path", execution_id=self.execution_id)
            return None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize filename for safe file operations."""
        return "".join(c if c.isalnum() or c in "- _" else "_" for c in name)

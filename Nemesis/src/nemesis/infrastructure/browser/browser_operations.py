"""Browser operations for trace, screenshots, and video."""
import traceback
from pathlib import Path

from playwright.sync_api import Page

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class BrowserOperations:
    """Handles browser trace, screenshot, and video operations."""

    def __init__(self, page: Page, execution_id: str) -> None:
        """Initialize browser operations."""
        self.page = page
        self.context = page.context
        self.execution_id = execution_id
        self.logger = Logger.get_instance({})

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(RuntimeError, AttributeError, OSError, IOError, Exception),
        specific_message="Failed to get video path: {error}",
        fallback_message="Failed to get video path: {error}",
        return_on_error=None
    )
    def get_video_path(self) -> Path | None:
        """Get video path if recording is enabled."""
        video = self.page.video
        if video:
            return Path(video.path())
        return None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize filename for safe file operations."""
        return "".join(c if c.isalnum() or c in "- _" else "_" for c in name)

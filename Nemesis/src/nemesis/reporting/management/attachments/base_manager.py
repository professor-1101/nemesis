"""Base class for attachment managers with shared functionality."""

import shutil
from pathlib import Path

from nemesis.core.logging import Logger


class BaseAttachmentManager:
    """Base class for attachment managers with shared functionality.

    Provides common initialization and file storage methods for
    metrics, trace, and video managers.
    """

    def __init__(self, reporter_manager, execution_manager):
        """Initialize base attachment manager.

        Args:
            reporter_manager: Reporter manager instance
            execution_manager: Execution manager instance
        """
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager
        self.execution_manager = execution_manager

    def _store_attachment_locally(self, src: Path, subdir: str, custom_name: str | None = None) -> Path:
        """Copy attachment into execution directory and return copied path.

        Args:
            src: Source file path
            subdir: Subdirectory name in execution directory
            custom_name: Optional custom filename (defaults to src.name)

        Returns:
            Path to the copied file

        Raises:
            OSError, IOError, PermissionError, shutil.Error: On file I/O errors
            KeyboardInterrupt, SystemExit: Always re-raised
            Exception: Other unexpected errors
        """
        try:
            dest_dir = self.execution_manager.get_execution_path() / subdir
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / (custom_name if custom_name else src.name)
            shutil.copy2(src, dest_path)
            self.logger.debug(f"Attachment stored locally: {dest_path}")
            return dest_path
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            # File I/O errors - directory creation or file copy failed
            self.logger.warning(f"Failed to store attachment locally ({src}) - I/O error: {e}", exc_info=True)
            raise
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # Always re-raise these to allow proper program termination
            # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from file operations
            # NOTE: shutil.copy2 or Path.mkdir may raise various exceptions we cannot predict
            self.logger.warning(f"Failed to store attachment locally ({src}): {e}", exc_info=True)
            raise

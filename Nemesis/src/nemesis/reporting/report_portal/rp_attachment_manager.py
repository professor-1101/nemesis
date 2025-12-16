"""ReportPortal attachment management module.

This module provides functionality for attaching files to ReportPortal test items,
handling file validation, size limits, and attachment to the appropriate test item
hierarchy (step > test > feature > launch).
"""
from pathlib import Path
from nemesis.utils.decorators import retry
from .rp_base_manager import RPBaseManager
from .rp_utils import RPUtils

class RPAttachmentManager(RPBaseManager):
    """Manages file attachments for ReportPortal test items.
    
    Handles file validation, size limits, and attachment to the appropriate
    test item hierarchy (step > test > feature > launch).
    """
    MAX_FILE_SIZE_MB = 32
    MAX_ATTACHMENT_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    def _get_current_item_id(self) -> str | None:
        """Get current item ID for attachment.

        Priority: step_id > test_id > feature_id > launch_id (as fallback)
        """
        # Try step first (most specific)
        step_id = self.rp_step_manager.get_step_id()
        if step_id:
            return step_id

        # Try test/scenario (even if finished, we might have the ID stored)
        test_id = self.rp_test_manager.get_test_id()
        if test_id:
            return test_id

        # Try feature
        feature_id = self.rp_feature_manager.get_feature_id()
        if feature_id:
            return feature_id

        # Last resort: use launch_id (attach to launch level)
        # This ensures attachments are never lost
        launch_id = self.rp_launch_manager.get_launch_id()
        return launch_id

    @retry(max_attempts=2, delay=1.0)
    def attach_file(self, file_path: Path, _description: str = "", _attachment_type: str = "") -> None:
        """Attach file with validation and filtering support.

        Args:
            file_path: Path to the file to attach
            _description: Description of the attachment (unused, kept for interface compatibility)
            _attachment_type: Type of attachment (unused, kept for interface compatibility)
        """
        if not file_path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return

        file_size = file_path.stat().st_size
        if file_size == 0:
            self.logger.warning(f"Skipping empty file: {file_path.name}")
            return

        if file_size > self.MAX_ATTACHMENT_SIZE_BYTES:
            self.logger.warning(
                f"File too large to attach: {file_path.name} "
                f"({file_size / 1024 / 1024:.1f}MB > {self.MAX_FILE_SIZE_MB}MB)"
            )
            # Log a message to ReportPortal about the large file
            item_id = self._get_current_item_id()
            launch_id = self.rp_launch_manager.get_launch_id()
            if item_id and launch_id:
                self.client.log(
                    time=RPUtils.timestamp(),
                    message=f"File '{file_path.name}' too large to attach "
                            f"({file_size / 1024 / 1024:.1f}MB)",
                    level="WARN",
                    item_id=item_id,
                )
            return

        item_id = self._get_current_item_id()
        launch_id = self.rp_launch_manager.get_launch_id()

        if not launch_id:
            self.logger.warning(f"No active launch to attach to: {file_path.name}")
            return

        # If no item_id, we'll attach to launch level (item_id can be None for launch-level attachments)
        if not item_id:
            self.logger.debug(f"No active item ID, attaching to launch level: {file_path.name}")
            item_id = None  # RP allows None for launch-level attachments

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            # Use minimal message - just filename to minimize log visibility
            # The attachment will appear in Attachments tab
            # Note: ReportPortal API always creates a log entry when attaching files
            # We use TRACE level and minimal message to reduce visibility in logs
            # Users can filter by "ATTACHMENT_ONLY" to hide these if needed
            message = f"ATTACHMENT_ONLY: {file_path.name}"

            # RPClient.log() does NOT accept launch_id parameter
            # It uses the launch_id from the client's internal state
            self.client.log(
                time=RPUtils.timestamp(),
                message=message,
                level="TRACE",  # Use TRACE level to minimize visibility in logs
                attachment={
                    "name": file_path.name,
                    "data": file_data,
                    "mime": RPUtils.get_mime_type(file_path)
                },
                item_id=item_id
            )

            self.logger.info(
                f"Attached: {file_path.name} ({file_size / 1024:.1f}KB)"
            )

        except (OSError, IOError, PermissionError) as e:
            # File I/O errors - file read failed
            self.logger.error(f"Failed to attach {file_path.name} - I/O error: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - client.log() or file access failed
            self.logger.error(f"Failed to attach {file_path.name} - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK client.log() may raise various exceptions we cannot predict
            self.logger.error(f"Failed to attach {file_path.name}: {e}", exc_info=True)

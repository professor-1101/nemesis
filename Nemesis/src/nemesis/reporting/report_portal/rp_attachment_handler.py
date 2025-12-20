"""ReportPortal attachment management module.

This module provides functionality for attaching files to ReportPortal test items,
handling file validation, size limits, and attachment to the appropriate test item
hierarchy (step > test > feature > launch).
"""
from pathlib import Path
from nemesis.utils.decorators import retry
from .rp_base_handler import RPBaseHandler
from .rp_utils import RPUtils

class RPAttachmentHandler(RPBaseHandler):
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

    def _generate_attachment_name(self, original_name: str, attachment_type: str = "") -> str:
        """Generate attachment name with proper naming convention.

        Format: feature__scenario__step__collectorType__timestamp.ext

        Args:
            original_name: Original filename
            attachment_type: Type of attachment (network, performance, screenshot, etc.)

        Returns:
            Formatted attachment name
        """
        from datetime import datetime
        import re

        # Get context from environment
        context = {}
        try:
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()
            if env_manager:
                context = env_manager.get_attachment_context()
        except Exception:
            # Fallback if context not available
            context = {"feature": "unknown", "scenario": "unknown", "step": "unknown"}

        # Sanitize names for filename
        def sanitize(text: str) -> str:
            return re.sub(r'[^\w\-_.]', '_', text)[:50]  # Limit length

        feature = sanitize(context.get("feature", "unknown"))
        scenario = sanitize(context.get("scenario", "unknown"))
        step = sanitize(context.get("step", "unknown"))

        # Determine collector type from attachment_type or filename
        collector_type = attachment_type or "unknown"
        if "network" in original_name.lower() or "har" in original_name.lower():
            collector_type = "network"
        elif "performance" in original_name.lower() or "metrics" in original_name.lower():
            collector_type = "performance"
        elif "screenshot" in original_name.lower() or "png" in original_name.lower():
            collector_type = "screenshot"
        elif "video" in original_name.lower() or "mp4" in original_name.lower():
            collector_type = "video"
        elif "console" in original_name.lower():
            collector_type = "console"

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

        # Extract extension
        name_parts = original_name.rsplit('.', 1)
        if len(name_parts) == 2:
            ext = name_parts[1]
        else:
            ext = ""

        # Build final name - keep it short for readability
        if collector_type == "screenshot":
            final_name = f"{step}_screenshot_{timestamp}.png"
        elif collector_type == "video":
            final_name = f"{step}_video_{timestamp}.mp4"
        elif collector_type == "network":
            final_name = f"network_logs_{timestamp}.json"
        elif collector_type == "console":
            final_name = f"console_logs_{timestamp}.txt"
        elif collector_type == "performance":
            final_name = f"performance_{timestamp}.json"
        else:
            final_name = f"{collector_type}_{timestamp}.{ext}" if ext else f"{collector_type}_{timestamp}"

        return final_name

    @retry(max_attempts=2, delay=1.0)
    def attach_file(self, file_data, _description: str = "", _attachment_type: str = "") -> None:
        """Attach file with validation and filtering support.

        Args:
            file_data: Path to file or bytes data to attach
            _description: Description of the attachment (unused, kept for interface compatibility)
            _attachment_type: Type of attachment (unused, kept for interface compatibility)
        """
        # Handle both Path and bytes input
        if isinstance(file_data, Path):
            if not file_data.exists():
                self.logger.warning(f"File not found: {file_data}")
                return
            file_size = file_data.stat().st_size
            file_content = None
        else:
            # Assume bytes
            file_size = len(file_data)
            file_content = file_data

        if file_size == 0:
            self.logger.warning("Skipping empty file/data")
            return

        if file_size > self.MAX_ATTACHMENT_SIZE_BYTES:
            file_name = getattr(file_data, 'name', 'data') if isinstance(file_data, Path) else 'data'
            self.logger.warning(
                f"Data too large to attach: {file_name} "
                f"({file_size / 1024 / 1024:.1f}MB > {self.MAX_FILE_SIZE_MB}MB)"
            )
            # Log a message to ReportPortal about the large file
            item_id = self._get_current_item_id()
            launch_id = self.rp_launch_manager.get_launch_id()
            if item_id and launch_id:
                self.client.log(
                    time=RPUtils.timestamp(),
                    message=f"File '{file_name}' too large to attach "
                            f"({file_size / 1024 / 1024:.1f}MB)",
                    level="WARN",
                    item_id=item_id,
                )
            return

        item_id = self._get_current_item_id()
        launch_id = self.rp_launch_manager.get_launch_id()

        if not launch_id:
            file_name = getattr(file_data, 'name', 'data') if isinstance(file_data, Path) else 'data'
            self.logger.warning(f"No active launch to attach to: {file_name}")
            return

        # If no item_id, we'll attach to launch level (item_id can be None for launch-level attachments)
        if not item_id:
            file_name = getattr(file_data, 'name', 'data') if isinstance(file_data, Path) else 'data'
            self.logger.debug(f"No active item ID, attaching to launch level: {file_name}")
            item_id = None  # RP allows None for launch-level attachments

        try:
            # Handle both Path and bytes
            if isinstance(file_data, Path):
                with open(file_data, "rb") as f:
                    file_content = f.read()
                file_name = file_data.name
            else:
                file_content = file_data
                file_name = f"data_{_attachment_type}" if _attachment_type else "data"

            # Generate proper attachment name with naming convention
            attachment_name = self._generate_attachment_name(file_name, _attachment_type)

            # Ensure we have a filename for mime type detection
            mime_filename = attachment_name if attachment_name else file_name

            # Use minimal message - just filename to minimize log visibility
            # The attachment will appear in Attachments tab
            # Note: ReportPortal API always creates a log entry when attaching files
            # We use TRACE level and minimal message to reduce visibility in logs
            message = attachment_name

            # RPClient.log() does NOT accept launch_id parameter
            # It uses the launch_id from the client's internal state
            # Determine MIME type based on file extension
            import os
            _, ext = os.path.splitext(attachment_name)
            mime_type = RPUtils.get_mime_type_from_ext(ext)
            self.client.log(
                time=RPUtils.timestamp(),
                message=message,
                level="TRACE",  # Use TRACE level to minimize visibility in logs
                attachment={
                    "name": attachment_name,
                    "data": file_content,
                    "mime": mime_type
                },
                item_id=item_id
            )

            self.logger.info(
                f"Attached: {file_name} ({file_size / 1024:.1f}KB)"
            )

        except (OSError, IOError, PermissionError) as e:
            # File I/O errors - file read failed
            self.logger.error(f"Failed to attach {file_name} - I/O error: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - client.log() or file access failed
            self.logger.error(f"Failed to attach {file_name} - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK client.log() may raise various exceptions we cannot predict
            self.logger.error(f"Failed to attach {file_name}: {e}", exc_info=True)

"""Video attachment management."""

from pathlib import Path
from nemesis.utils.video_converter import convert_to_mp4
from .base_handler import BaseAttachmentHandler


class VideoHandler(BaseAttachmentHandler):
    """Handles video attachments."""

    def _convert_video(self, video_path: Path) -> Path:
        """
        Convert video to MP4 format before processing.
        This ensures all videos are in MP4 format regardless of reporter type.
        """
        converted = convert_to_mp4(video_path)
        if converted and converted != video_path:
            self.logger.debug(f"Video converted: {video_path.name} -> {converted.name}")
            return converted
        # If conversion failed or already MP4, return original
        return converted if converted else video_path

    def _store_video_locally(self, src: Path, subdir: str) -> Path:
        """Copy video attachment into execution directory with .mp4 extension.

        Args:
            src: Source video file path
            subdir: Subdirectory name in execution directory

        Returns:
            Path to the copied file (with .mp4 extension)
        """
        # Ensure .mp4 extension for stored video
        dest_name = src.stem + ".mp4" if src.suffix.lower() != ".mp4" else src.name
        return self._store_attachment_locally(src, subdir, custom_name=dest_name)

    def attach_video(self, video_path: Path) -> None:
        """
        Attach a video (local storage + optional ReportPortal upload).

        Video is converted to MP4 format BEFORE any storage/upload operations.
        This ensures compatibility across all reporter types.
        """
        if not isinstance(video_path, Path):
            video_path = Path(video_path)

        if not video_path.exists():
            self.logger.warning(f"Video file not found: {video_path}")
            return

        # STEP 1: Convert to MP4 FIRST (before any storage/upload)
        converted_path = self._convert_video(video_path)

        if not converted_path.exists():
            self.logger.warning(f"Converted video file not found: {converted_path}")
            return

        # STEP 2: Local handling (if enabled)
        if self.reporter_manager.is_local_enabled():
            try:
                if hasattr(self.reporter_manager.get_local_reporter(), "add_attachment"):
                    self.reporter_manager.get_local_reporter().add_attachment(
                        converted_path, "video", "Test Execution Video"
                    )
                else:
                    self._store_video_locally(converted_path, "videos")
            except (OSError, IOError, PermissionError) as e:
                # File I/O errors from _store_attachment_locally (re-raised) - non-critical
                self.logger.debug(f"Failed to handle local video attachment - I/O error: {e}", exc_info=True)
            except (AttributeError, RuntimeError) as e:
                # Local reporter API errors - non-critical
                self.logger.debug(f"Failed to handle local video attachment - API error: {e}", exc_info=True)
            except (KeyboardInterrupt, SystemExit):
                # Allow program interruption to propagate
                raise
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter or file operations
                # NOTE: Local reporter or file operations may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to handle local video attachment: {e}", exc_info=True)

        # STEP 3: ReportPortal handling (if enabled)
        if self.reporter_manager.is_rp_healthy():
            try:
                # Attach as file (attachment will appear in Attachments tab)
                # The attach_file method creates a minimal log entry automatically
                self.reporter_manager.get_rp_client().attach_file(
                    converted_path, "Test Execution Video", "video"
                )
            except (AttributeError, RuntimeError) as e:
                # ReportPortal attachment API errors - non-critical
                self.logger.debug(f"Failed to attach video to ReportPortal - API error: {e}", exc_info=True)
            except (OSError, IOError) as e:
                # File I/O errors from converted_path access - non-critical
                self.logger.debug(f"Failed to attach video to ReportPortal - I/O error: {e}", exc_info=True)
            except (KeyboardInterrupt, SystemExit):
                # Allow program interruption to propagate
                raise
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to attach video to ReportPortal: {e}", exc_info=True)

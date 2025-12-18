"""Video processing service for browser artifacts.

Converts WebM video files to MP4 format for compatibility with reporting systems.
"""

import subprocess
import traceback
from pathlib import Path

from nemesis.infrastructure.logging import Logger


# Video processing constants
VIDEO_CONVERSION_BATCH_LOG_THRESHOLD = 1
VIDEO_FINALIZATION_DELAY = 0.5  # Seconds to wait after context close


class VideoProcessingService:
    """
    Converts video files from WebM to MP4 format.

    Processes individual files or entire directories, handling errors gracefully
    to prevent conversion failures from blocking browser operations.
    """

    def __init__(self, logger: Logger | None = None):
        """
        Initialize video processing service.

        Args:
            logger: Logger instance for logging (optional, creates if not provided)
        """
        self.logger = logger or Logger.get_instance({})

    def convert_videos_in_directory(self, video_dir: Path) -> None:
        """
        Convert all WebM videos in directory to MP4.

        This ensures videos are converted for BOTH local storage AND ReportPortal.
        Videos converted here will be in MP4 format when VideoHandler.attach_video()
        is called, or will be ready for direct RP upload.

        Args:
            video_dir: Directory containing WebM video files

        Example:
            >>> service = VideoProcessingService()
            >>> service.convert_videos_in_directory(Path("./videos"))
        """
        try:
            if not video_dir.exists():
                return

            # Find all WebM files
            webm_files = list(video_dir.glob("*.webm"))
            if not webm_files:
                return

            self.logger.info(
                f"Converting {len(webm_files)} video(s) to MP4 (for all reporters)..."
            )

            # Convert each file
            for webm_file in webm_files:
                self._convert_single_video(webm_file)

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (OSError, ImportError) as e:
            # Video conversion setup errors
            self.logger.warning(
                f"Video conversion error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="VideoProcessingService",
                method="convert_videos_in_directory"
            )

    def _convert_single_video(self, webm_file: Path) -> Path | None:
        """
        Convert a single WebM video file to MP4.

        Args:
            webm_file: Path to WebM file

        Returns:
            Path to MP4 file if successful, None otherwise
        """
        try:
            # Import here to avoid dependency if not needed
            from nemesis.utils.video_converter import convert_to_mp4  # pylint: disable=import-outside-toplevel

            mp4_file = convert_to_mp4(webm_file)
            if mp4_file and mp4_file != webm_file:
                self.logger.debug(f"Converted: {webm_file.name} -> {mp4_file.name}")
                return mp4_file

            return None

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (OSError, RuntimeError, subprocess.SubprocessError) as e:
            # Video conversion errors for single file - log and continue
            self.logger.warning(
                f"Failed to convert {webm_file.name}: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="VideoProcessingService",
                method="_convert_single_video",
                video_file=str(webm_file)
            )
            return None

    def find_videos_to_convert(self, video_dir: Path) -> list[Path]:
        """
        Find all WebM videos in directory that need conversion.

        Args:
            video_dir: Directory to search

        Returns:
            List of WebM file paths
        """
        if not video_dir.exists():
            return []

        return list(video_dir.glob("*.webm"))

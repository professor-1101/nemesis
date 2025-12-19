"""Simple video converter adapter for MP4 conversion.

Uses imageio-ffmpeg which embeds ffmpeg binaries automatically.
No separate installation required.
"""
import subprocess
import traceback
from pathlib import Path
from typing import Optional

from nemesis.infrastructure.logging import Logger


def convert_to_mp4(input_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Simple adapter to convert video to MP4 format.

    Args:
        input_path: Path to input video file (e.g., .webm)
        output_path: Optional output path (default: same location with .mp4 extension)

    Returns:
        Path to converted MP4 file, or original path if conversion fails/not available
    """
    logger = Logger.get_instance({})

    if not input_path.exists():
        logger.warning(f"Video file not found: {input_path}")
        return None

    # Skip if already MP4
    if input_path.suffix.lower() == '.mp4':
        logger.debug("Video is already MP4 format")
        return input_path

    # Get ffmpeg binary
    try:
        import imageio_ffmpeg  # pylint: disable=import-outside-toplevel
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        logger.warning("imageio-ffmpeg not installed, skipping conversion")
        return input_path
    except (AttributeError, RuntimeError) as e:
        # imageio-ffmpeg API errors
        logger.warning(f"Failed to get ffmpeg - API error: {e}", traceback=traceback.format_exc(), module=__name__, function="convert_to_mp4")
        return input_path
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from imageio_ffmpeg
        # NOTE: imageio_ffmpeg may raise various exceptions we cannot predict
        logger.warning(f"Failed to get ffmpeg: {e}, skipping conversion", traceback=traceback.format_exc(), module=__name__, function="convert_to_mp4")
        return input_path

    # Generate output path
    if output_path is None:
        output_path = input_path.with_suffix('.mp4')
    else:
        output_path = Path(output_path).with_suffix('.mp4')

    try:
        logger.info(f"Converting video to MP4: {input_path.name}")

        # Simple ffmpeg command: convert to MP4 with H.264/AAC
        cmd = [
            ffmpeg_exe,
            "-i", str(input_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "medium",
            "-crf", "23",
            "-movflags", "+faststart",
            "-y",
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0 and output_path.exists():
            logger.info(f"Video converted: {output_path.name}")
            # Remove original webm file
            try:
                input_path.unlink()
            except (OSError, PermissionError):
                # File deletion errors - non-critical, just log
                logger.debug(f"Failed to remove original video file: {input_path}", module=__name__, function="convert_to_mp4")
            except Exception:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from file deletion
                # NOTE: Path.unlink may raise various exceptions we cannot predict
                logger.debug(f"Failed to remove original video file: {input_path}", module=__name__, function="convert_to_mp4")
            return output_path
        logger.warning(f"Conversion failed, using original: {result.stderr[:200]}")
        return input_path

    except subprocess.TimeoutExpired:
        logger.warning("Video conversion timed out, using original")
        return input_path
    except (OSError, subprocess.SubprocessError) as e:
        # Subprocess execution errors
        logger.warning(f"Conversion error - subprocess failed: {e}, using original", traceback=traceback.format_exc(), module=__name__, function="convert_to_mp4", input_path=str(input_path))
        return input_path
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from subprocess operations
        # NOTE: subprocess.run may raise various exceptions we cannot predict
        logger.warning(f"Conversion error: {e}, using original", traceback=traceback.format_exc(), module=__name__, function="convert_to_mp4", input_path=str(input_path))
        return input_path

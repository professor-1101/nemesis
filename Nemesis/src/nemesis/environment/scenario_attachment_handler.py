"""Scenario attachment handling for reporting."""
import time
import traceback
from typing import Any, Optional

from nemesis.core.logging import Logger
from nemesis.environment.collector_content_logger import CollectorContentLogger
from nemesis.reporting.manager import ReportManager


class ScenarioAttachmentHandler:
    """Handles attachment of videos and collector data for scenarios."""

    def __init__(self, report_manager: Optional[ReportManager]):
        """Initialize scenario attachment handler.

        Args:
            report_manager: Report manager instance
        """
        self.report_manager = report_manager
        self.logger = Logger.get_instance({})

    def attach_videos(self, _context: Any, _scenario: Any) -> None:
        """Attach videos from Playwright videos directory to reports.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            _scenario: Behave scenario object (unused, kept for interface compatibility)
        """
        try:
            if not self.report_manager or not self.report_manager.execution_manager:
                return

            execution_path = self.report_manager.execution_manager.get_execution_path()
            if not execution_path:
                return

            videos_dir = execution_path / "videos"
            if not videos_dir.exists():
                return

            # Wait a bit for video conversion to complete (happens in browser_lifecycle._cleanup_resources)
            time.sleep(1.5)  # Give time for MP4 conversion

            # Find the most recent MP4 video (converted from webm)
            mp4_videos = sorted(videos_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not mp4_videos:
                # If no MP4, try webm (conversion might not have happened yet)
                webm_videos = sorted(videos_dir.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
                if webm_videos:
                    # Use webm if MP4 conversion hasn't happened yet
                    latest_video = webm_videos[0]
                    try:
                        self.report_manager.attach_video(latest_video)
                        self.logger.debug(f"Attached video (webm) to reports: {latest_video.name}")
                    except (OSError, IOError) as e:
                        # Video file I/O errors
                        self.logger.warning(f"Failed to attach video {latest_video.name} - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos", video_file=str(latest_video))
                    except (AttributeError, RuntimeError) as e:
                        # ReportPortal attachment API errors
                        self.logger.warning(f"Failed to attach video {latest_video.name} - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos", video_file=str(latest_video))
                    except (KeyboardInterrupt, SystemExit):
                        # Allow program interruption to propagate
                        raise
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        # Catch-all for unexpected errors from video attachment
                        # NOTE: Video attachment operations may raise various exceptions we cannot predict
                        self.logger.warning(f"Failed to attach video {latest_video.name}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos", video_file=str(latest_video))
                return

            # Attach the most recent MP4 video (should be from this scenario)
            latest_video = mp4_videos[0]
            # Check if video was created recently (within last 5 minutes)
            current_time = time.time()
            video_age = current_time - latest_video.stat().st_mtime
            if video_age < 300:  # Within last 5 minutes
                try:
                    self.report_manager.attach_video(latest_video)
                    self.logger.debug(f"Attached video to reports: {latest_video.name}")
                except (OSError, IOError) as e:
                    # Video file I/O errors
                    self.logger.warning(f"Failed to attach video {latest_video.name} - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos", video_file=str(latest_video))
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors
                    self.logger.warning(f"Failed to attach video {latest_video.name} - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos", video_file=str(latest_video))
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from video attachment
                    # NOTE: Video attachment operations may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to attach video {latest_video.name}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos", video_file=str(latest_video))
            else:
                self.logger.debug(f"Skipping old video: {latest_video.name} (age: {video_age:.1f}s)")

        except (OSError, IOError) as e:
            # File system errors - video directory access failed
            self.logger.debug(f"Error attaching scenario videos - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos")
        except (AttributeError, RuntimeError) as e:
            # ReportPortal API errors
            self.logger.debug(f"Error attaching scenario videos - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos")
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from video attachment operations
            # NOTE: Video directory operations or ReportPortal API may raise various exceptions we cannot predict
            self.logger.debug(f"Error attaching scenario videos: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_videos")

    def attach_collectors(self, _context: Any, _scenario: Any) -> None:
        """Attach collector files (console, network, performance) to reports.

        Files are attached both as attachments and as logs with content for filtering and dashboard creation.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            _scenario: Behave scenario object (unused, kept for interface compatibility)
        """
        try:
            if not self.report_manager or not self.report_manager.execution_manager:
                return

            execution_path = self.report_manager.execution_manager.get_execution_path()
            if not execution_path:
                return

            # Use collector content logger
            content_logger = CollectorContentLogger(self.report_manager)

            # Attach console logs - read content and log each entry
            console_file = execution_path / "console" / "console.jsonl"
            if console_file.exists() and console_file.stat().st_size > 0:
                try:
                    # Attach as file (which creates both attachment and log entry)
                    self.report_manager.attach_file(
                        console_file,
                        "Console Logs",
                        "console"
                    )
                    # Read file content and log each line as a separate log entry
                    content_logger.log_console_content(console_file)
                    self.logger.debug(f"Attached console logs to reports: {console_file.name}")
                except (OSError, IOError) as e:
                    # File I/O errors
                    self.logger.warning(f"Failed to attach console logs {console_file.name} - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(console_file))
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors
                    self.logger.warning(f"Failed to attach console logs {console_file.name} - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(console_file))
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from console attachment
                    # NOTE: File operations or ReportPortal API may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to attach console logs {console_file.name}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(console_file))

            # Attach network metrics - read content and log structured data
            network_file = execution_path / "network" / "network_metric.json"
            if network_file.exists() and network_file.stat().st_size > 0:
                try:
                    # Attach as file (which creates both attachment and log entry)
                    self.report_manager.attach_file(
                        network_file,
                        "Network Metrics",
                        "network"
                    )
                    # Read file content and log structured metrics
                    content_logger.log_network_content(network_file)
                    self.logger.debug(f"Attached network metrics to reports: {network_file.name}")
                except (OSError, IOError) as e:
                    # File I/O errors
                    self.logger.warning(f"Failed to attach network metrics {network_file.name} - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(network_file))
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors
                    self.logger.warning(f"Failed to attach network metrics {network_file.name} - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(network_file))
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from network attachment
                    # NOTE: File operations or ReportPortal API may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to attach network metrics {network_file.name}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(network_file))

            # Attach performance metrics - read content and log structured data
            performance_file = execution_path / "performance" / "performance_metrics.json"
            if performance_file.exists() and performance_file.stat().st_size > 0:
                try:
                    # Attach as metrics (which creates both attachment and log entry)
                    self.report_manager.attach_metrics(
                        performance_file,
                        "performance"
                    )
                    # Read file content and log structured metrics
                    content_logger.log_performance_content(performance_file)
                    self.logger.debug(f"Attached performance metrics to reports: {performance_file.name}")
                except (OSError, IOError) as e:
                    # File I/O errors
                    self.logger.warning(f"Failed to attach performance metrics {performance_file.name} - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(performance_file))
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors
                    self.logger.warning(f"Failed to attach performance metrics {performance_file.name} - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(performance_file))
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from performance attachment
                    # NOTE: File operations or ReportPortal API may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to attach performance metrics {performance_file.name}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors", file_path=str(performance_file))

        except (OSError, IOError) as e:
            # File system errors - collector directory access failed
            self.logger.debug(f"Error attaching scenario collectors - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors")
        except (AttributeError, RuntimeError) as e:
            # ReportPortal API errors
            self.logger.debug(f"Error attaching scenario collectors - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors")
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from collector attachment operations
            # NOTE: Collector directory operations or ReportPortal API may raise various exceptions we cannot predict
            self.logger.debug(f"Error attaching scenario collectors: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioAttachmentHandler", method="attach_collectors")

"""Attachment management for reporting."""

from nemesis.reporting.management.attachments.screenshot_manager import ScreenshotManager
from nemesis.reporting.management.attachments.video_manager import VideoManager
from nemesis.reporting.management.attachments.trace_manager import TraceManager
from nemesis.reporting.management.attachments.metrics_manager import MetricsManager


class AttachmentManager:
    """Manages file attachments."""

    def __init__(self, reporter_manager, execution_manager):
        """Initialize attachment manager."""
        self.screenshot_manager = ScreenshotManager(reporter_manager, execution_manager)
        self.video_manager = VideoManager(reporter_manager, execution_manager)
        self.trace_manager = TraceManager(reporter_manager, execution_manager)
        self.metrics_manager = MetricsManager(reporter_manager, execution_manager)

    def attach_screenshot(self, screenshot: bytes, name: str) -> None:
        """Attach screenshot to reports."""
        self.screenshot_manager.attach_screenshot(screenshot, name)

    def attach_video(self, video_path) -> None:
        """Attach a video (local storage + optional ReportPortal upload)."""
        self.video_manager.attach_video(video_path)

    def attach_trace(self, trace_path) -> None:
        """Attach a Playwright trace (local storage + optional ReportPortal upload)."""
        self.trace_manager.attach_trace(trace_path)

    def attach_metrics(self, metrics_path, metric_type: str) -> None:
        """Attach metrics file (local storage + optional ReportPortal upload)."""
        self.metrics_manager.attach_metrics(metrics_path, metric_type)

    def attach_file(self, file_path, description: str = "", attachment_type: str = "") -> None:
        """Attach file to reports with optional attachment_type for filtering.

        Args:
            file_path: Path to file to attach
            description: Description of the attachment
            attachment_type: Type of attachment (e.g., 'har', 'console', 'metrics', 'screenshot', 'video', 'trace')
        """
        self.metrics_manager.attach_file(file_path, description, attachment_type)

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message to reports."""
        self.metrics_manager.log_message(message, level)

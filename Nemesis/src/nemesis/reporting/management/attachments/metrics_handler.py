"""Metrics attachment management."""
from pathlib import Path
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback
from .base_handler import BaseAttachmentHandler


class MetricsHandler(BaseAttachmentHandler):
    """Handles metrics attachments."""

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError, OSError, IOError),
        specific_message="Failed to handle local attachment: {error}",
        fallback_message="Failed to handle local attachment: {error}"
    )
    def _call_local_reporter(self, callback) -> None:
        """Call local reporter with exception handling."""
        callback()

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to call ReportPortal: {error}",
        fallback_message="Failed to call ReportPortal: {error}"
    )
    def _call_rp_client(self, callback) -> None:
        """Call ReportPortal client with exception handling."""
        callback()

    def attach_metrics(self, metrics_path: Path, metric_type: str) -> None:
        """Attach metrics file (local storage + optional ReportPortal upload)."""
        if not isinstance(metrics_path, Path):
            metrics_path = Path(metrics_path)

        if not metrics_path.exists():
            self.logger.warning(f"Metrics file not found: {metrics_path}")
            return

        metric_type_clean = (metric_type or "metrics").lower()
        desc = f"{metric_type_clean.title()} Metrics"

        if self.reporter_manager.is_local_enabled():
            def _attach_local():
                if hasattr(self.reporter_manager.get_local_reporter(), "add_attachment"):
                    self.reporter_manager.get_local_reporter().add_attachment(metrics_path, metric_type_clean, desc)
                else:
                    # store under a directory named after metric_type
                    self._store_attachment_locally(metrics_path, metric_type_clean + "s")
            self._call_local_reporter(_attach_local)

        if self.reporter_manager.is_rp_healthy():
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().attach_file(metrics_path, desc, "metrics")
            )

    def attach_file(self, file_path: Path, description: str = "", attachment_type: str = "") -> None:
        """Attach file to reports with optional attachment_type for filtering.

        Args:
            file_path: Path to file to attach
            description: Description of the attachment
            attachment_type: Type of attachment (e.g., 'har', 'console', 'metrics')
                           If not provided, will be inferred from file path/extension
        """
        if not file_path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return

        # If attachment_type not provided, try to infer from file extension/path
        if not attachment_type:
            if file_path.suffix.lower() == '.har':
                attachment_type = "har"
            elif file_path.suffix.lower() in ['.jsonl', '.log', '.txt'] and 'console' in str(file_path).lower():
                attachment_type = "console"
            elif file_path.suffix.lower() in ['.json'] and 'network' in str(file_path).lower():
                attachment_type = "network"
            elif file_path.suffix.lower() in ['.json'] and 'performance' in str(file_path).lower():
                attachment_type = "metrics"

        if self.reporter_manager.is_rp_healthy():
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().attach_file(file_path, description, attachment_type)
            )

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message to reports."""
        if self.reporter_manager.is_local_enabled():
            self._call_local_reporter(
                lambda: self.reporter_manager.get_local_reporter().add_log(message, level)
            )

        if self.reporter_manager.is_rp_healthy():
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().log_message(message, level)
            )

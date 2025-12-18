"""Metrics attachment management."""
import traceback
from pathlib import Path
from .base_handler import BaseAttachmentHandler


class MetricsManager(BaseAttachmentHandler):
    """Manages metrics attachments."""

    def attach_metrics(self, metrics_path: Path, metric_type: str) -> None:
        """Attach metrics file (local storage + optional ReportPortal upload)."""
        if not isinstance(metrics_path, Path):
            metrics_path = Path(metrics_path)

        if not metrics_path.exists():
            self.logger.warning(f"Metrics file not found: {metrics_path}")
            return

        metric_type_clean = (metric_type or "metrics").lower()
        desc = f"{metric_type_clean.title()} Metrics"

        try:
            if self.reporter_manager.is_local_enabled() and hasattr(self.reporter_manager.get_local_reporter(), "add_attachment"):
                self.reporter_manager.get_local_reporter().add_attachment(metrics_path, metric_type_clean, desc)
            elif self.reporter_manager.is_local_enabled():
                # store under a directory named after metric_type
                self._store_attachment_locally(metrics_path, metric_type_clean + "s")
        except (AttributeError, RuntimeError) as e:
            # Local reporter API errors - non-critical
            self.logger.debug(f"Failed to handle local metrics attachment - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_metrics")
        except (OSError, IOError) as e:
            # File I/O errors from _store_attachment_locally (re-raised)
            self.logger.debug(f"Failed to handle local metrics attachment - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_metrics")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from local reporter or file operations
            # NOTE: Local reporter or file operations may raise various exceptions we cannot predict
            self.logger.debug(f"Failed to handle local metrics attachment: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_metrics")

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().attach_file(metrics_path, desc, "metrics")
            except (AttributeError, RuntimeError) as e:
                # ReportPortal attachment API errors - non-critical
                self.logger.debug(f"Failed to attach metrics to ReportPortal - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_metrics")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to attach metrics to ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_metrics")

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

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().attach_file(file_path, description, attachment_type)
            except (AttributeError, RuntimeError) as e:
                # ReportPortal attachment API errors - non-critical
                self.logger.debug(f"Failed to attach file to RP - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_file")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to attach file to RP: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="attach_file")

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message to reports."""
        if self.reporter_manager.is_local_enabled():
            try:
                self.reporter_manager.get_local_reporter().add_log(message, level)
            except (AttributeError, RuntimeError) as e:
                # Local reporter API errors - non-critical
                self.logger.debug(f"Failed to add log to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="log_message")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: LocalReporter.add_log may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to add log to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="log_message")

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().log_message(message, level)
            except (AttributeError, RuntimeError) as e:
                # ReportPortal API errors - non-critical
                self.logger.debug(f"Failed to log message to RP - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="log_message")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to log message to RP: {e}", traceback=traceback.format_exc(), module=__name__, class_name="MetricsManager", method="log_message")

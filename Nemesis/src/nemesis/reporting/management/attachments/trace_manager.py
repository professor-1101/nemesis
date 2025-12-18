"""Trace attachment management."""
import shutil
from pathlib import Path
from .base_handler import BaseAttachmentHandler


class TraceManager(BaseAttachmentHandler):
    """Manages trace attachments."""

    def attach_trace(self, trace_path: Path) -> None:
        """Attach a Playwright trace (local storage + optional ReportPortal upload)."""
        if not isinstance(trace_path, Path):
            trace_path = Path(trace_path)

        if not trace_path.exists():
            self.logger.warning(f"Trace file not found: {trace_path}")
            return

        try:
            if self.reporter_manager.is_local_enabled() and hasattr(self.reporter_manager.get_local_reporter(), "add_attachment"):
                self.reporter_manager.get_local_reporter().add_attachment(trace_path, "trace", "Playwright Trace")
            elif self.reporter_manager.is_local_enabled():
                self._store_attachment_locally(trace_path, "traces")
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            # File I/O errors from _store_attachment_locally (re-raised) - non-critical
            self.logger.debug(f"Failed to handle local trace attachment - I/O error: {e}", exc_info=True)
        except (AttributeError, RuntimeError) as e:
            # Local reporter API errors - non-critical
            self.logger.debug(f"Failed to handle local trace attachment - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from local reporter or file operations
            # NOTE: Local reporter or file operations may raise various exceptions we cannot predict
            self.logger.debug(f"Failed to handle local trace attachment: {e}", exc_info=True)

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().attach_file(trace_path, "Playwright Trace", "trace")
            except (AttributeError, RuntimeError) as e:
                # ReportPortal attachment API errors - non-critical
                self.logger.debug(f"Failed to attach trace to ReportPortal - API error: {e}", exc_info=True)
            except (OSError, IOError) as e:
                # File I/O errors from trace_path access - non-critical
                self.logger.debug(f"Failed to attach trace to ReportPortal - I/O error: {e}", exc_info=True)
            except (KeyboardInterrupt, SystemExit):
                # Allow program interruption to propagate
                raise
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to attach trace to ReportPortal: {e}", exc_info=True)

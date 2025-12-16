"""Console logs collection."""
import re
import threading
import traceback
from pathlib import Path
from typing import Any

from playwright.sync_api import ConsoleMessage, Page

from nemesis.core.exceptions import CollectorError
from nemesis.core.logging import Logger
from nemesis.utils import get_path_manager
from nemesis.utils.helpers.exception_helpers import ensure_directory_exists
from .base_collector import BaseCollector


class ConsoleCollector(BaseCollector):
    """Collects browser console logs."""

    MAX_LOGS = 10000  # Prevent memory issues
    MAX_MESSAGE_LENGTH = 5000  # Truncate long messages

    def __init__(self, page: Page, filter_levels: list[str] | None = None, ignore_patterns: list[str] | None = None) -> None:
        self.page = page
        self.logger = Logger.get_instance({})
        self.filter_levels = self._validate_filter_levels(filter_levels)
        self.ignore_patterns = self._compile_ignore_patterns(ignore_patterns)
        self.logs: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._listener_active = False

        self._setup_listener()
        self._bound_handler = self._on_console_message

    def _compile_ignore_patterns(self, patterns: list[str] | None) -> list[re.Pattern]:
        """Compile a list of regex patterns."""
        compiled = []
        if patterns:
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern))
                except re.error as e:
                    self.logger.warning(f"Invalid regex ignore pattern '{pattern}': {e}, skipping.")
        return compiled

    def _validate_filter_levels(
        self, filter_levels: list[str] | None
    ) -> list[str]:
        """Validate and normalize filter levels."""
        valid_levels = {
            "log", "debug", "info", "error", "warning",
            "dir", "dirxml", "table", "trace", "clear",
            "startGroup", "startGroupCollapsed", "endGroup",
            "assert", "profile", "profileEnd", "count", "timeEnd"
        }

        if filter_levels is None:
            return ["error", "warning"]

        # Normalize and validate
        normalized = []
        for level in filter_levels:
            level_lower = level.lower()
            if level_lower in valid_levels:
                normalized.append(level_lower)
            else:
                self.logger.warning(
                    f"Invalid console level '{level}', skipping"
                )

        return normalized if normalized else ["error", "warning"]

    def _setup_listener(self) -> None:
        """Setup console message listener."""
        try:
            self.page.on("console", self._on_console_message)
            self._listener_active = True
            self.logger.debug(
                f"Console listener setup: filtering {self.filter_levels}"
            )
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Playwright page event listener errors
            self.logger.error(f"Failed to setup console listener: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ConsoleCollector", method="_setup_listener")
            raise CollectorError("Failed to setup console listener", str(e)) from e

    def _on_console_message(self, msg: ConsoleMessage) -> None:
        """Handle console message event."""
        try:
            msg_type = msg.type
            msg_text = msg.text

            # Check ignore patterns first
            for pattern in self.ignore_patterns:
                if pattern.search(msg_text):
                    self.logger.debug(f"Ignoring console message by pattern: [{msg_type.upper()}] {msg_text[:100]}...")
                    return

            if msg_type not in self.filter_levels:
                return

            # Check log limit with FIFO behavior
            with self._lock:
                # Remove oldest if at limit (FIFO)
                if len(self.logs) >= self.MAX_LOGS:
                    self.logs.pop(0)  # Remove oldest log
                    if len(self.logs) == self.MAX_LOGS - 1:  # Log only once
                        self.logger.warning(
                            f"Console log limit reached ({self.MAX_LOGS}), "
                            "using FIFO behavior"
                        )

                # Truncate long messages
                text = msg_text
                if len(text) > self.MAX_MESSAGE_LENGTH:
                    text = text[:self.MAX_MESSAGE_LENGTH] + "... [truncated]"

                log_entry = {
                    "type": msg_type,
                    "text": text,
                    "location": self._format_location(msg.location),
                    "timestamp": self._get_timestamp(),
                }

                self.logs.append(log_entry)

            # Log to framework logger
            if msg_type == "error":
                self.logger.error(f"Console Error: {text[:200]}")
            elif msg_type == "warning":
                self.logger.warning(f"Console Warning: {text[:200]}")

        except (AttributeError, RuntimeError) as e:
            # Message processing errors - log but don't fail
            self.logger.debug(f"Failed to log console message: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ConsoleCollector", method="_on_console_message")
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise

    def _format_location(self, location: dict[str, Any]) -> str:
        """Format location info as readable string."""
        if not location:
            return "unknown"

        url = location.get("url", "unknown")
        line = location.get("lineNumber", "?")
        col = location.get("columnNumber", "?")

        # Truncate long URLs
        if len(url) > 100:
            url = "..." + url[-97:]

        return f"{url}:{line}:{col}"

    def get_errors(self) -> list[dict[str, Any]]:
        """Get only error logs (thread-safe)."""
        with self._lock:
            return [log for log in self.logs if log["type"] == "error"]

    def get_warnings(self) -> list[dict[str, Any]]:
        """Get only warning logs (thread-safe)."""
        with self._lock:
            return [log for log in self.logs if log["type"] == "warning"]

    def get_summary(self) -> dict[str, int]:
        """Get log count summary by type."""
        with self._lock:
            summary: dict[str, int] = {}
            for log in self.logs:
                log_type = log["type"]
                summary[log_type] = summary.get(log_type, 0) + 1
            return summary

    def save_to_file(self, execution_id: str, _scenario_name: str) -> Path:
        """Save console logs to file."""
        try:
            # Use PathManager for centralized path management
            try:
                path_manager = get_path_manager()
                file_path = path_manager.get_attachment_path(execution_id, "console", "console.jsonl")
            except (AttributeError, KeyError, RuntimeError) as e:
                # PathManager initialization errors - fallback to original logic
                self.logger.debug(f"PathManager failed, using fallback path: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ConsoleCollector", method="save_to_file", execution_id=execution_id)
                file_path = Path(f"reports/{execution_id}/console/console.jsonl")
                ensure_directory_exists(file_path, execution_id)
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
                raise

            with self._lock:
                logs_to_save = self.logs.copy()

            if not logs_to_save:
                self.logger.debug("No console logs to save")
                # Create empty file with header
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("=" * 70 + "\n")
                    f.write("CONSOLE LOGS SUMMARY\n")
                    f.write("=" * 70 + "\n")
                    f.write("No console logs captured during this session.\n")
                    f.write("=" * 70 + "\n")
                return file_path

            with open(file_path, "w", encoding="utf-8") as f:
                # Write summary header
                summary = self.get_summary()
                f.write("=" * 70 + "\n")
                f.write("CONSOLE LOGS SUMMARY\n")
                f.write("=" * 70 + "\n")
                for log_type, count in sorted(summary.items()):
                    f.write(f"{log_type.upper():15} {count:5} messages\n")
                f.write("=" * 70 + "\n\n")

                # Write logs
                for log in logs_to_save:
                    f.write(f"[{log['type'].upper()}] {log['text']}\n")
                    if log.get("location"):
                        f.write(f"  Location: {log['location']}\n")
                    f.write(f"  Time: {log['timestamp']:.0f}ms\n")
                    f.write("\n")

            self.logger.info(
                f"Console logs saved: {file_path} ({len(logs_to_save)} entries)"
            )
            return file_path

        except (OSError, IOError, PermissionError) as e:
            # File system errors
            self.logger.error(f"Failed to save console logs: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ConsoleCollector", method="save_to_file", execution_id=execution_id)
            raise CollectorError("Failed to save console logs", str(e)) from e
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # Always re-raise these to allow proper program termination
            # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
            raise

    def _cleanup_listeners(self) -> None:
        """Clean up console listener."""
        if self._listener_active:
            # Detach listener to avoid events after shutdown
            self.page.off("console", self._bound_handler)
            self._listener_active = False

    def dispose(self) -> None:
        """Detach listeners and clear resources explicitly."""
        try:
            if self._listener_active:
                self.page.off("console", self._bound_handler)
        except (AttributeError, RuntimeError) as e:
            # Playwright page event listener errors - ignore during cleanup
            self.logger.debug(f"Error detaching console listener during dispose: {e}", module=__name__, class_name="ConsoleCollector", method="dispose")
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        self._listener_active = False

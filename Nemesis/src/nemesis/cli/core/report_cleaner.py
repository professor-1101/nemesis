"""Report cleanup utilities."""
import shutil
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from nemesis.core.logging import Logger
from nemesis.utils.helpers import FileUtils
from .report_base import ReportBase

LOGGER = Logger.get_instance({})


class ReportCleaner(ReportBase):
    """Handles cleanup of old test reports."""

    def find_old_reports(self, older_than: str) -> List[Path]:
        """Find reports older than specified duration."""
        if not self.reports_dir.exists():
            return []

        threshold = self._parse_duration(older_than)
        cutoff_time = datetime.now() - threshold

        old_reports = []

        for report_dir in self.reports_dir.iterdir():
            if not report_dir.is_dir():
                continue

            modified_time = datetime.fromtimestamp(report_dir.stat().st_mtime)

            if modified_time < cutoff_time:
                old_reports.append(report_dir)

        return sorted(old_reports, key=lambda x: x.stat().st_mtime)

    def delete_reports(self, reports: List[Path]) -> int:
        """Delete specified report directories."""
        deleted_count = 0

        for report_dir in reports:
            try:
                shutil.rmtree(report_dir)
                deleted_count += 1
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # Always re-raise these to allow proper program termination
                # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                raise
            except (OSError, PermissionError, shutil.Error) as e:
                # File deletion errors - log but continue with other files
                LOGGER.warning(f"Failed to delete report directory {report_dir}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportCleaner", method="delete_reports", report_dir=str(report_dir))

        return deleted_count

    def calculate_total_size(self, reports: List[Path]) -> str:
        """Calculate total size of reports in human-readable format."""
        total_bytes = 0

        for report_dir in reports:
            total_bytes += self._get_dir_size(report_dir)

        return self._format_size(total_bytes)

    def _get_dir_size(self, directory: Path) -> int:
        """Get directory size in bytes."""
        return FileUtils.calculate_dir_size(directory)

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} TB"

    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse duration string to timedelta."""
        if not duration_str:
            raise ValueError("Duration cannot be empty")

        unit = duration_str[-1].lower()

        try:
            value = int(duration_str[:-1])
        except ValueError as exc:
            raise ValueError(f"Invalid duration format: {duration_str}") from exc

        if unit == "d":
            return timedelta(days=value)
        if unit == "h":
            return timedelta(hours=value)
        if unit == "m":
            return timedelta(minutes=value)
        raise ValueError(
            f"Invalid duration unit: {unit}. Use d (days), h (hours), or m (minutes)"
        )

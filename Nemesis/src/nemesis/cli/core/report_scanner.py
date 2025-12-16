"""Report directory scanner and analyzer."""
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from nemesis.core.logging import Logger
from nemesis.utils.helpers import FileUtils
from .report_base import ReportBase

LOGGER = Logger.get_instance({})


class ReportScanner(ReportBase):
    """Scans and analyzes test report directories."""

    def scan_reports(
            self,
            limit: int = 10,
            sort_by: str = "date",
    ) -> List[Dict[str, Any]]:
        """Scan report directories and return execution info."""
        if not self.reports_dir.exists():
            return []

        executions = []

        for report_dir in self.reports_dir.iterdir():
            if not report_dir.is_dir():
                continue

            execution_info = self._parse_execution(report_dir)
            if execution_info:
                executions.append(execution_info)

        executions = self._sort_executions(executions, sort_by)

        return executions[:limit]

    def _parse_execution(self, report_dir: Path) -> Dict[str, Any] | None:
        """Parse execution directory and extract info."""
        try:
            parts = report_dir.name.split("_")

            if len(parts) < 3:
                # Try to parse anyway
                exec_id = report_dir.name
                date_str = "N/A"
                time_str = "N/A"
            else:
                date_str = parts[0]
                time_str = parts[1]
                exec_id = parts[2]

            modified_time = report_dir.stat().st_mtime
            modified_dt = datetime.fromtimestamp(modified_time)

            status = self._detect_status(report_dir)

            return {
                "id": exec_id,
                "date": date_str,
                "time": time_str,
                "timestamp": modified_time,
                "datetime": modified_dt,
                "status": status,
                "path": report_dir,
                "size": self._calculate_dir_size(report_dir),
            }
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (OSError, ValueError, AttributeError) as e:
            # File system or parsing errors - skip this directory
            LOGGER.debug(f"Failed to parse execution directory {report_dir}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportScanner", method="_parse_execution", report_dir=str(report_dir))
            return None

    def _detect_status(self, report_dir: Path) -> str:
        """Detect execution status from report artifacts."""
        # Check for report.html
        report_html = report_dir / "report.html"
        if report_html.exists():
            try:
                content = report_html.read_text(encoding="utf-8")
                if "failed" in content.lower() or "error" in content.lower():
                    return "failed"
                if "passed" in content.lower() or "success" in content.lower():
                    return "passed"
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # Always re-raise these to allow proper program termination
                # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                raise
            except (OSError, IOError, UnicodeDecodeError) as e:
                # File read errors - continue to next detection method
                LOGGER.debug(f"Failed to read report.html for status detection: {e}", module=__name__, class_name="ReportScanner", method="_detect_status", report_dir=str(report_dir))

        # Check for behave JSON output
        json_report = report_dir / "report.json"
        if json_report.exists():
            try:
                import json  # pylint: disable=import-outside-toplevel
                with open(json_report, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Analyze JSON structure for status
                    if isinstance(data, list):
                        for feature in data:
                            if "status" in feature and feature["status"] == "failed":
                                return "failed"
                return "passed"
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # Always re-raise these to allow proper program termination
                # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                raise
            except (OSError, IOError, json.JSONDecodeError, UnicodeDecodeError) as e:
                # File read or JSON parsing errors - continue to unknown status
                LOGGER.debug(f"Failed to read or parse report.json for status detection: {e}", module=__name__, class_name="ReportScanner", method="_detect_status", report_dir=str(report_dir))

        return "unknown"

    def _calculate_dir_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes."""
        return FileUtils.calculate_dir_size(directory)

    def _sort_executions(
            self,
            executions: List[Dict[str, Any]],
            sort_by: str,
    ) -> List[Dict[str, Any]]:
        """Sort executions by specified criteria."""
        if sort_by == "date":
            return sorted(executions, key=lambda x: x["timestamp"], reverse=True)
        if sort_by == "status":
            # Sort by status (failed, passed, unknown)
            status_order = {"failed": 0, "passed": 1, "unknown": 2}
            return sorted(
                executions,
                key=lambda x: status_order.get(x["status"], 3),
            )
        if sort_by == "duration":
            # Sort by timestamp (oldest first)
            return sorted(executions, key=lambda x: x["timestamp"])

        return executions

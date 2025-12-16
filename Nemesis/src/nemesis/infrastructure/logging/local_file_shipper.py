"""Local File Shipper - Ships logs to local files

Simple file-based logging for when SigNoz is not available.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from nemesis.domain.ports import ILogShipper


class LocalFileShipper(ILogShipper):
    """
    Adapter: Local File Log Shipper

    Ships logs to local JSON file.

    Clean Architecture:
    - Implements ILogShipper interface
    - Infrastructure layer adapter
    """

    def __init__(self, log_file_path: Path):
        """
        Initialize local file shipper

        Args:
            log_file_path: Path to log file
        """
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create/open log file
        self._file = open(self.log_file_path, "a", encoding="utf-8")

    def ship(self, log_entry: Dict[str, Any]) -> bool:
        """
        Ship a single log entry

        Args:
            log_entry: Log entry dictionary

        Returns:
            True if shipped successfully
        """
        try:
            # Write as JSON line
            self._file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            self._file.flush()
            return True
        except Exception as e:
            print(f"[LocalFileShipper] Failed to write log: {e}")
            return False

    def ship_batch(self, log_entries: List[Dict[str, Any]]) -> bool:
        """
        Ship multiple log entries

        Args:
            log_entries: List of log entries

        Returns:
            True if all shipped successfully
        """
        try:
            for log_entry in log_entries:
                self._file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            self._file.flush()
            return True
        except Exception as e:
            print(f"[LocalFileShipper] Failed to write logs: {e}")
            return False

    def flush(self) -> None:
        """Flush pending writes"""
        self._file.flush()

    def close(self) -> None:
        """Close file"""
        self._file.close()

    def get_channel_name(self) -> str:
        """Get channel name"""
        return "local_file"

    def is_healthy(self) -> bool:
        """Check if shipper is healthy"""
        return not self._file.closed

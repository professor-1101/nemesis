"""Local file channel for log shipping."""

import json
import os
from pathlib import Path
from typing import Any, Dict

from ...config.settings import LocalConfig

# Try to use fast JSON library, fallback to standard json
def _json_dumps_fallback(x):
    """JSON dumps fallback function."""
    return json.dumps(x, ensure_ascii=False, default=str).encode('utf-8')

try:
    import orjson
    JSON_DUMPS = orjson.dumps
    BINARY_MODE = True
except ImportError:
    JSON_DUMPS = _json_dumps_fallback
    BINARY_MODE = False


class LocalChannel:
    """Local file channel for log shipping."""

    def __init__(self, config: LocalConfig):
        """Initialize local channel."""
        self.config = config
        self._current_file = None
        self._file_handle = None

    def _get_output_path(self, log_data: Dict[str, Any]) -> Path:
        """Get output path based on execution_id in log data with security validation."""
        import re

        # Extract execution_id from log data or environment
        execution_id = log_data.get('execution_id')
        if not execution_id:
            execution_id = os.environ.get('NEMESIS_EXECUTION_ID')
            if not execution_id:
                # Generate a proper execution ID instead of using 'unknown'
                from nemesis.shared.execution_context import ExecutionContext
                execution_id = ExecutionContext.get_execution_id()

        # Sanitize execution_id to prevent path traversal
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', execution_id)

        # Use PathManager for centralized path management
        try:
            from nemesis.utils import get_path_manager
            path_manager = get_path_manager()
            return path_manager.get_logs_path(safe_id, self.config.filename_template)
        except Exception:
            # Fallback to original logic with security check
            output_dir = self.config.output_dir.replace('{execution_id}', safe_id)
            output_path = Path(output_dir).resolve()  # Resolve symlinks

            # Validate path is inside reports/ directory
            base_path = Path('reports').resolve()
            if not str(output_path).startswith(str(base_path)):
                raise ValueError(f"Invalid path: {output_path}")

            output_path.mkdir(parents=True, exist_ok=True)
            filename = self.config.filename_template
            return output_path / filename

    def send_log(self, log_data: Dict[str, Any]) -> bool:
        """Send log to local file with file handle reuse."""
        try:
            file_path = self._get_output_path(log_data)

            # Reuse file handle if same path
            if self._current_file != file_path:
                if self._file_handle:
                    self._file_handle.close()
                self._file_handle = open(file_path, 'a', encoding='utf-8')
                self._current_file = file_path

            # Use fast JSON serialization
            json_data = JSON_DUMPS(log_data)
            if BINARY_MODE:
                self._file_handle.write(json_data + b'\n')
            else:
                self._file_handle.write(json_data.decode('utf-8') + '\n')
            self._file_handle.flush()

            return True

        except Exception as e:
            import logging
            logger = logging.getLogger("nemesis.local_channel")
            logger.error(f"Failed to write to local file: {e}")
            return False

    def __del__(self):
        """Cleanup file handle on destruction."""
        if self._file_handle:
            try:
                self._file_handle.close()
            except Exception:
                pass

    def get_status(self) -> Dict[str, Any]:
        """Get channel status."""
        try:
            # Check for test_execution.jsonl files in reports directories
            reports_dir = Path("reports")
            if reports_dir.exists():
                log_files = list(reports_dir.rglob("test_execution.jsonl"))
                total_size = sum(f.stat().st_size for f in log_files if f.exists())

                return {
                    "type": "local",
                    "output_dir": "reports/{execution_id}/logs/",
                    "file_count": len(log_files),
                    "total_size_bytes": total_size,
                    "status": "connected"
                }
            else:
                return {
                    "type": "local",
                    "output_dir": "reports/{execution_id}/logs/",
                    "file_count": 0,
                    "total_size_bytes": 0,
                    "status": "no_reports_dir"
                }
        except Exception as e:
            return {
                "type": "local",
                "status": "error",
                "error": str(e)
            }

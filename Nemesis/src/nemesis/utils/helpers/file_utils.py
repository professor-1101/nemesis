"""File utility functions."""
import traceback
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict


class FileUtils:
    """File utility functions."""

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Ensure directory exists."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            raise OSError(f"Failed to create directory {path}: {e}") from e

    @staticmethod
    def read_json_file(file_path: Path) -> Dict[str, Any]:
        """Read and parse JSON file with validation."""
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError(f"JSON root must be object, got {type(data).__name__}")

            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e

    @staticmethod
    def write_json_file(
        file_path: Path,
        data: Dict[str, Any],
        indent: int = 2,
        backup: bool = False
    ) -> None:
        """Write data to JSON file."""
        # Create backup if requested
        if backup and file_path.exists():
            backup_path = file_path.with_suffix('.json.bak')
            try:
                shutil.copy2(file_path, backup_path)
            except (OSError, IOError, PermissionError, shutil.Error) as e:
                log_entry = {
                    "timestamp": __import__('time').time(),
                    "level": "WARNING",
                    "message": f"Failed to create backup: {e}",
                    "component": "file_utils",
                    "backup_path": str(backup_path),
                    "exception_type": type(e).__name__
                }
                # Use proper logging instead of print
                logger = logging.getLogger("nemesis.file_utils")
                logger.warning(json.dumps(log_entry, ensure_ascii=False))
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from shutil.copy2
                # NOTE: shutil.copy2 may raise various exceptions we cannot predict
                log_entry = {
                    "timestamp": __import__('time').time(),
                    "level": "WARNING",
                    "message": f"Failed to create backup: {e}",
                    "component": "file_utils",
                    "backup_path": str(backup_path),
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
                logger = logging.getLogger("nemesis.file_utils")
                logger.warning(json.dumps(log_entry, ensure_ascii=False))

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Failed to write JSON to {file_path}: {e}") from e

    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file hash."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        hasher = hashlib.new(algorithm)

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}") from e

        return hasher.hexdigest()

    @staticmethod
    def calculate_dir_size(directory: Path) -> int:
        """Calculate total size of directory in bytes.

        Args:
            directory: Path to directory

        Returns:
            Total size in bytes
        """
        total_size = 0

        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except (OSError, PermissionError):
            # File access errors - return partial size
            # Non-critical, just return what we calculated so far
            pass

        return total_size

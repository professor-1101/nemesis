"""Path utilities for centralized path management."""

import os
from pathlib import Path
from typing import Optional


class PathManager:
    """Centralized path management with configuration support."""

    def __init__(self, config_loader=None):
        """Initialize path manager.

        Args:
            config_loader: ConfigLoader instance for getting paths from config
        """
        self.config_loader = config_loader

    def get_reports_dir(self) -> Path:
        """Get reports directory from config or environment."""
        if self.config_loader:
            reports_dir = self.config_loader.get("reports_dir")
            if reports_dir:
                return Path(reports_dir)

        # Fallback to environment variable or default
        reports_dir = os.getenv("NEMESIS_REPORTS_DIR", "reports")
        return Path(reports_dir)

    def get_features_dir(self) -> Path:
        """Get features directory from config or environment."""
        if self.config_loader:
            features_dir = self.config_loader.get("features_dir")
            if features_dir:
                return Path(features_dir)

        # Fallback to environment variable or default
        features_dir = os.getenv("NEMESIS_FEATURES_DIR", "features")
        return Path(features_dir)

    def get_execution_path(self, execution_id: str) -> Path:
        """Get execution directory path."""
        reports_dir = self.get_reports_dir()
        return reports_dir / execution_id

    def get_attachment_path(self, execution_id: str, attachment_type: str,
                           filename: str) -> Path:
        """Get attachment file path."""
        execution_path = self.get_execution_path(execution_id)
        attachment_dir = execution_path / attachment_type
        attachment_dir.mkdir(parents=True, exist_ok=True)
        return attachment_dir / filename

    def get_logs_path(self, execution_id: str, filename: str = "test_execution.jsonl") -> Path:
        """Get logs file path."""
        execution_path = self.get_execution_path(execution_id)
        logs_dir = execution_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir / filename


# Global instance for backward compatibility
_path_manager: Optional[PathManager] = None


def get_path_manager(config_loader=None) -> PathManager:
    """Get global path manager instance."""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager(config_loader)
    return _path_manager


def set_path_manager(path_manager: PathManager) -> None:
    """Set global path manager instance."""
    global _path_manager
    _path_manager = path_manager

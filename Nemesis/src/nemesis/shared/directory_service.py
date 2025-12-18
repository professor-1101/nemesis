"""Centralized directory management with configuration-driven approach."""
import traceback
from pathlib import Path
from typing import Dict, Optional, Set
from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger


class DirectoryService:
    """Manages directory creation based on centralized configuration."""

    def __init__(self, config: ConfigLoader):
        """Initialize directory manager.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.logger = Logger.get_instance({})
        self._created_directories: Set[Path] = set()

    def should_create_directory(self, directory_type: str) -> bool:
        """Check if directory should be created based on config.

        Args:
            directory_type: Type of directory (screenshots, videos, traces, etc.)

        Returns:
            True if directory should be created
        """
        # Check if local reporting is enabled first
        local_enabled = self._get_bool_config("reporting.local.enabled", True)
        if not local_enabled:
            return False

        # Check specific attachment type
        attachment_key = f"attachments.{directory_type}.enabled"
        return self._get_bool_config(attachment_key, self._get_default_for_type(directory_type))

    def get_execution_base_path(self, execution_id: str) -> Path:
        """Get base execution path.

        Args:
            execution_id: Execution identifier

        Returns:
            Base path for execution
        """
        reports_dir = self.config.get("reports_dir", "reports")
        return Path(reports_dir) / execution_id

    def create_execution_directories(self, execution_id: str) -> Dict[str, Path]:
        """Create execution directories based on configuration.

        Args:
            execution_id: Execution identifier

        Returns:
            Dictionary of created directory paths
        """
        base_path = self.get_execution_base_path(execution_id)
        created_dirs = {}

        # Always create logs directory if local reporting is enabled
        if self._get_bool_config("reporting.local.enabled", True):
            logs_dir = base_path / "logs"
            self._create_directory(logs_dir)
            created_dirs["logs"] = logs_dir

        # LAZY CREATION: Only create base execution directory and logs
        # Attachment directories will be created on-demand when first file is saved
        self.logger.info(f"Created base execution directory for {execution_id}: {list(created_dirs.keys())}")
        return created_dirs

    def get_attachment_path(self, execution_id: str, attachment_type: str, filename: str) -> Optional[Path]:
        """Get attachment file path and create directory on-demand if needed.

        Args:
            execution_id: Execution identifier
            attachment_type: Type of attachment
            filename: File name

        Returns:
            Path to attachment file or None if directory shouldn't exist
        """
        if not self.should_create_directory(attachment_type):
            return None

        base_path = self.get_execution_base_path(execution_id)
        attachment_dir = base_path / attachment_type

        # LAZY CREATION: Create attachment directory on-demand
        self._create_directory(attachment_dir)

        return attachment_dir / filename

    def _create_directory(self, dir_path: Path) -> None:
        """Create directory if not already created.

        Args:
            dir_path: Directory path to create
        """
        if dir_path not in self._created_directories:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self._created_directories.add(dir_path)
            except (OSError, PermissionError) as e:
                # File system errors - directory creation failed
                self.logger.warning(f"Failed to create directory {dir_path}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="DirectoryService", method="_create_directory", dir_path=str(dir_path))
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from Path.mkdir
                # NOTE: Path.mkdir may raise various exceptions we cannot predict
                self.logger.warning(f"Failed to create directory {dir_path}: {e}", traceback=traceback.format_exc(), module=__name__, class_name="DirectoryService", method="_create_directory", dir_path=str(dir_path))

    def _get_bool_config(self, key: str, default: bool) -> bool:
        """Get boolean config value with proper type conversion.

        Args:
            key: Configuration key
            default: Default value

        Returns:
            Boolean value
        """
        value = self.config.get(key, default)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    def _get_default_for_type(self, directory_type: str) -> bool:
        """Get default enabled state for directory type.

        Args:
            directory_type: Type of directory

        Returns:
            Default enabled state
        """
        defaults = {
            "screenshots": True,
            "videos": False,  # Videos are resource-intensive
            "traces": True,
            "network": True,
            "performance": True,
            "console": True,
        }
        return defaults.get(directory_type, True)

    def cleanup(self) -> None:
        """Cleanup directory manager resources."""
        self._created_directories.clear()
        self.logger.debug("Directory manager cleaned up")

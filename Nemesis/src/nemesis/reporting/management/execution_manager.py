"""Execution management for reporting with config-driven architecture."""

from pathlib import Path

from nemesis.infrastructure.config import ConfigLoader
from nemesis.shared.directory_service import DirectoryService
from nemesis.infrastructure.logging import Logger
from nemesis.shared.execution_context import ExecutionContext


class ExecutionManager:
    """Manages execution directory and ID with config-driven structure."""

    def __init__(self, config: ConfigLoader):
        """Initialize execution manager.

        Args:
            config: Centralized config loader
        """
        self.config = config
        self.logger = Logger.get_instance({})
        self.execution_id = ExecutionContext.get_execution_id()
        self.execution_path = self._create_execution_directory()

    def _create_execution_directory(self) -> Path:
        """Create execution directory structure based on config."""
        # Use DirectoryService for centralized directory management
        directory_manager = DirectoryService(self.config)

        # Create directories based on configuration
        created_dirs = directory_manager.create_execution_directories(self.execution_id)

        if created_dirs:
            base_path = created_dirs.get("logs", directory_manager.get_execution_base_path(self.execution_id)).parent
            self.logger.info(f"Execution directory created: {base_path}")
            return base_path
        # Fallback if no directories were created
        base_path = directory_manager.get_execution_base_path(self.execution_id)
        self.logger.info(f"Execution directory (no subdirs): {base_path}")
        return base_path

    def get_execution_id(self) -> str:
        """Get execution ID."""
        return self.execution_id

    def get_execution_path(self) -> Path:
        """Get execution directory path."""
        return self.execution_path

    def start_execution(self) -> None:
        """Start execution tracking."""
        try:
            self.logger.info(f"Execution started: {self.execution_id}")
            self.logger.info(f"Execution directory: {self.execution_path}")
        except Exception as e:
            self.logger.error(f"Failed to start execution: {e}")
            raise

    def end_execution(self) -> None:
        """End execution tracking."""
        try:
            self.logger.info(f"Execution ended: {self.execution_id}")
        except Exception as e:
            self.logger.error(f"Failed to end execution: {e}")
            raise

    def cleanup(self) -> None:
        """Cleanup execution resources."""
        try:
            self.logger.info("Execution cleanup completed")
        except Exception as e:
            self.logger.error(f"Failed to cleanup execution: {e}")
            raise

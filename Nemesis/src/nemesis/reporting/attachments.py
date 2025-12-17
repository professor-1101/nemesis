"""Attachment handling for reports."""
import json
from pathlib import Path
from typing import Any

from nemesis.infrastructure.logging import Logger


class AttachmentHandler:
    """Handles attachments for various reporters."""

    def __init__(self, execution_path: Path) -> None:
        self.execution_path = execution_path
        self.logger = Logger.get_instance({})

    def save_metrics(
        self, metrics: dict[str, Any], scenario_name: str, metric_type: str
    ) -> Path:
        """Save metrics to JSON."""
        filename = self._sanitize_filename(f"{scenario_name}_{metric_type}.json")
        file_path = self.execution_path / metric_type / filename

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
            raise

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize filename."""
        return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

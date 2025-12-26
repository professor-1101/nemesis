"""Network report file writer module.

Handles persistence of network metrics to JSON and HAR formats.
"""
import json
import traceback
from pathlib import Path
from typing import Any

from nemesis.infrastructure.logging import Logger
from nemesis.shared.exceptions import CollectorError
from nemesis.utils import get_path_manager
from nemesis.utils.helpers.exception_helpers import ensure_directory_exists


class NetworkReportWriter:
    """
    Writes network metrics and HAR data to files.

    Responsibilities:
    - Persist metrics to JSON format
    - Persist HAR data to .har format
    - Handle file system errors
    - Create directories as needed
    """

    def __init__(self):
        self.logger = Logger.get_instance({})

    def save_metrics(
        self,
        metrics: dict[str, Any],
        har_data: dict[str, Any],
        execution_id: str
    ) -> Path:
        """
        Save network metrics to JSON and HAR formats.

        Saves two files:
        1. network_metric.json - Custom format with Nemesis metrics
        2. network.har - Standard HAR 1.2 format (importable to Chrome DevTools)

        Args:
            metrics: Network metrics dictionary
            har_data: HAR format dictionary
            execution_id: Unique execution identifier

        Returns:
            Path to JSON metrics file

        Raises:
            CollectorError: If file save fails
        """
        try:
            # Use PathHelper for centralized path management
            try:
                path_manager = get_path_manager()
                json_file_path = path_manager.get_attachment_path(
                    execution_id, "network", "network_metric.json"
                )
                har_file_path = path_manager.get_attachment_path(
                    execution_id, "network", "network.har"
                )
            except (AttributeError, KeyError, RuntimeError) as e:
                # PathHelper initialization errors - fallback to original logic
                self.logger.debug(
                    f"PathHelper failed, using fallback path: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name="NetworkReportWriter",
                    method="save_metrics",
                    execution_id=execution_id
                )
                json_file_path = Path(f"reports/{execution_id}/network/network_metric.json")
                har_file_path = Path(f"reports/{execution_id}/network/network.har")
                ensure_directory_exists(json_file_path, execution_id)
            except (KeyboardInterrupt, SystemExit):
                # Always re-raise to allow proper program termination
                raise

            # Save custom JSON format
            self._write_json_file(json_file_path, metrics)
            self.logger.info(
                f"Network metrics (JSON) saved: {json_file_path} "
                f"({metrics['total_requests']} requests)"
            )

            # Save HAR format
            try:
                self._write_json_file(har_file_path, har_data)
                entry_count = len(har_data['log']['entries'])
                self.logger.info(
                    f"Network metrics (HAR) saved: {har_file_path} ({entry_count} entries)"
                )
            except Exception as har_error:  # pylint: disable=broad-exception-caught
                # HAR export is supplementary - don't fail if it errors
                self.logger.warning(f"Failed to save HAR format: {har_error}")

            return json_file_path

        except (OSError, IOError, PermissionError) as e:
            # File system errors
            self.logger.error(
                f"Failed to save network metrics: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="NetworkReportWriter",
                method="save_metrics",
                execution_id=execution_id
            )
            raise CollectorError("Failed to save network metrics", str(e)) from e
        except (TypeError, ValueError) as e:
            # JSON serialization errors
            self.logger.error(
                f"Failed to serialize network metrics: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="NetworkReportWriter",
                method="save_metrics",
                execution_id=execution_id
            )
            raise CollectorError("Failed to save network metrics", str(e)) from e
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise

    def _write_json_file(self, file_path: Path, data: dict[str, Any]) -> None:
        """
        Write dictionary to JSON file with proper encoding.

        Args:
            file_path: Path to write to
            data: Dictionary to serialize

        Raises:
            OSError: If file write fails
            ValueError: If JSON serialization fails
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

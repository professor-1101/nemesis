"""Helper functions for HAR (HTTP Archive) path configuration."""

from typing import Any


def add_har_path_to_options(
    options: dict[str, Any],
    directory_manager: Any,
    execution_id: str,
    logger: Any = None
) -> None:
    """Add HAR recording path to browser context options if enabled.
    
    Args:
        options: Browser context options dictionary to modify
        directory_manager: Directory manager instance for path resolution
        execution_id: Execution ID for path construction
        logger: Optional logger instance for debug messages
    """
    network_enabled = directory_manager.should_create_directory("network")

    if network_enabled:
        har_path = directory_manager.get_attachment_path(execution_id, "network", "requests.har")
        if har_path:
            options["record_har_path"] = str(har_path)
            if logger:
                logger.debug(f"HAR recording enabled: {har_path}")

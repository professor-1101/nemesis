"""Log Shipper Port - Interface for log shipping

This interface allows logs to be shipped to multiple destinations
(local file, SigNoz, Splunk, etc.) without coupling core logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ILogShipper(ABC):
    """
    Port: Log Shipper Interface

    Abstraction for shipping logs to various destinations.

    Implementations:
    - LocalFileShipper (ship to local files)
    - SigNozShipper (ship to SigNoz observability platform)
    - SplunkShipper (ship to Splunk)

    Clean Architecture:
    - Interface in Domain layer
    - Implementations in Infrastructure layer
    """

    @abstractmethod
    def ship(self, log_entry: Dict[str, Any]) -> bool:
        """
        Ship a single log entry

        Args:
            log_entry: Log entry dictionary

        Returns:
            True if shipped successfully, False otherwise
        """
        ...

    @abstractmethod
    def ship_batch(self, log_entries: List[Dict[str, Any]]) -> bool:
        """
        Ship multiple log entries in batch

        Args:
            log_entries: List of log entries

        Returns:
            True if all shipped successfully, False otherwise
        """
        ...

    @abstractmethod
    def flush(self) -> None:
        """Flush any pending log entries"""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close shipper and cleanup resources"""
        ...

    @abstractmethod
    def get_channel_name(self) -> str:
        """
        Get channel name for identification

        Returns:
            Channel name (e.g., "local_file", "signoz", "splunk")
        """
        ...

    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if shipper is healthy and can accept logs

        Returns:
            True if healthy, False otherwise
        """
        ...

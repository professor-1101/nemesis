"""Log shipping interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ILogShipper(ABC):
    """Port for log shipping"""

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
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def get_channel_name(self) -> str:
        ...

    @abstractmethod
    def is_healthy(self) -> bool:
        ...

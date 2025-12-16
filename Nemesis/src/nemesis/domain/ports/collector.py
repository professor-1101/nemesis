"""Data collection interface"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path


class ICollector(ABC):
    """Port for data collection"""

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def get_collected_data(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def save_to_file(self, output_path: Path) -> None:
        """
        Save collected data to file

        Args:
            output_path: Path to output file
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        ...

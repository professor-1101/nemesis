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
    def save_collected_data(
        self,
        execution_id: str,
        output_dir: Path,
        scenario_name: str = ""
    ) -> Path:
        """
        Save collected data to file

        Args:
            execution_id: Execution identifier
            output_dir: Output directory for saving data
            scenario_name: Optional scenario name

        Returns:
            Path to saved file
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        ...

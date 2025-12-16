"""Collector Port - Interface for data collection

This interface allows different collectors (console, network, performance)
to be implemented independently.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path


class ICollector(ABC):
    """
    Port: Collector Interface

    Abstraction for collecting data during test execution.

    Implementations:
    - ConsoleCollector (browser console logs)
    - NetworkCollector (network requests/responses)
    - PerformanceCollector (performance metrics)

    Clean Architecture:
    - Interface in Domain layer
    - Implementations in Infrastructure layer
    """

    @abstractmethod
    def start(self) -> None:
        """Start collecting data"""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop collecting data"""
        ...

    @abstractmethod
    def get_collected_data(self) -> List[Dict[str, Any]]:
        """
        Get collected data

        Returns:
            List of collected data items
        """
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
        """Clear collected data"""
        ...

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics

        Returns:
            Dictionary with summary statistics
        """
        ...

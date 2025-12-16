"""Reporter Port - Interface for test reporting

This interface allows multiple reporting backends without coupling core logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pathlib import Path

from nemesis.domain.entities import Execution, Scenario, Step


class IReporter(ABC):
    """
    Port: Reporter Interface

    Abstraction for test reporting to various backends.

    Implementations:
    - JSONReporter (simple JSON output)
    - ReportPortalReporter (ReportPortal integration)
    - ConsoleReporter (console output)

    Clean Architecture:
    - Interface in Domain layer
    - Implementations in Infrastructure layer
    """

    @abstractmethod
    def start_execution(self, execution: Execution) -> None:
        """
        Report execution start

        Args:
            execution: Execution entity
        """
        ...

    @abstractmethod
    def end_execution(self, execution: Execution) -> None:
        """
        Report execution end

        Args:
            execution: Execution entity
        """
        ...

    @abstractmethod
    def start_scenario(self, scenario: Scenario) -> None:
        """
        Report scenario start

        Args:
            scenario: Scenario entity
        """
        ...

    @abstractmethod
    def end_scenario(self, scenario: Scenario) -> None:
        """
        Report scenario end

        Args:
            scenario: Scenario entity
        """
        ...

    @abstractmethod
    def start_step(self, step: Step) -> None:
        """
        Report step start

        Args:
            step: Step entity
        """
        ...

    @abstractmethod
    def end_step(self, step: Step) -> None:
        """
        Report step end

        Args:
            step: Step entity
        """
        ...

    @abstractmethod
    def attach_file(
        self,
        file_path: Path,
        description: str = "",
        attachment_type: str = ""
    ) -> None:
        """
        Attach file to current test item

        Args:
            file_path: Path to file
            description: File description
            attachment_type: Type of attachment (screenshot, video, trace, etc.)
        """
        ...

    @abstractmethod
    def log_message(self, message: str, level: str = "INFO") -> None:
        """
        Log message to reporter

        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        ...

    @abstractmethod
    def generate_report(self, execution: Execution, output_dir: Path) -> Optional[Path]:
        """
        Generate final report

        Args:
            execution: Execution entity
            output_dir: Output directory

        Returns:
            Path to generated report (or None if not applicable)
        """
        ...

"""Test reporting interface"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pathlib import Path

from nemesis.domain.entities import Execution, Scenario, Step


class IReporter(ABC):
    """Port for test execution reporting"""

    @abstractmethod
    def start_execution(self, execution: Execution) -> None:
        ...

    @abstractmethod
    def end_execution(self, execution: Execution) -> None:
        ...

    @abstractmethod
    def start_scenario(self, scenario: Scenario) -> None:
        ...

    @abstractmethod
    def end_scenario(self, scenario: Scenario) -> None:
        ...

    @abstractmethod
    def start_step(self, step: Step) -> None:
        ...

    @abstractmethod
    def end_step(self, step: Step) -> None:
        ...

    @abstractmethod
    def attach_file(self, file_path: Path, description: str = "", attachment_type: str = "") -> None:
        ...

    @abstractmethod
    def log_message(self, message: str, level: str = "INFO") -> None:
        ...

    @abstractmethod
    def generate_report(self, execution: Execution, output_dir: Path) -> Optional[Path]:
        ...

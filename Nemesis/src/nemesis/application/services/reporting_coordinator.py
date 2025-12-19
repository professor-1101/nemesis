"""Reporting Coordinator - Manages reporters lifecycle"""

from typing import List
from pathlib import Path

from nemesis.domain.entities import Scenario, Step
from nemesis.domain.ports import IReporter, ILogger


class ReportingCoordinator:
    """
    Application Service: Reporting Coordinator

    Responsibilities (SRP):
    - Coordinate multiple reporters
    - Delegate reporting calls to all reporters
    - Handle reporter failures gracefully

    This replaces part of the old god class ReportCoordinator.
    """

    def __init__(self, reporters: List[IReporter], logger: ILogger):
        """
        Initialize with reporters

        Args:
            reporters: List of reporter implementations (Dependency Injection)
            logger: Logger implementation (Dependency Injection)
        """
        self.reporters = reporters
        self.logger = logger

    def start_scenario(self, scenario: Scenario) -> None:
        """Report scenario start to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.start_scenario(scenario)
            except Exception as e:
                self.logger.warning(f"Reporter {reporter.__class__.__name__} failed: {e}")

    def end_scenario(self, scenario: Scenario) -> None:
        """Report scenario end to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.end_scenario(scenario)
            except Exception as e:
                self.logger.warning(f"Reporter {reporter.__class__.__name__} failed: {e}")

    def start_step(self, step: Step) -> None:
        """Report step start to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.start_step(step)
            except Exception as e:
                self.logger.warning(f"Reporter {reporter.__class__.__name__} failed: {e}")

    def end_step(self, step: Step) -> None:
        """Report step end to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.end_step(step)
            except Exception as e:
                self.logger.warning(f"Reporter {reporter.__class__.__name__} failed: {e}")

    def attach_file(
        self,
        file_path: Path,
        description: str = "",
        attachment_type: str = ""
    ) -> None:
        """Attach file to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.attach_file(file_path, description, attachment_type)
            except Exception as e:
                self.logger.warning(f"Reporter {reporter.__class__.__name__} failed: {e}")

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.log_message(message, level)
            except Exception as e:
                self.logger.warning(f"Reporter {reporter.__class__.__name__} failed: {e}")

"""Execution Coordinator - Manages test execution lifecycle

This replaces the god class responsibilities from the old ReportManager.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from nemesis.domain.entities import Execution, Scenario
from nemesis.domain.value_objects import ExecutionId
from nemesis.domain.ports import IReporter
from nemesis.application.use_cases import GenerateExecutionReportUseCase


class ExecutionCoordinator:
    """
    Application Service: Execution Coordinator

    Responsibilities (Single Responsibility Principle):
    - Manage execution lifecycle
    - Create and track execution entity
    - Coordinate report generation at end

    This is NOT a god class - it has ONE clear responsibility: execution lifecycle.
    """

    def __init__(self, reporters: list[IReporter], output_dir: Path):
        """
        Initialize coordinator

        Args:
            reporters: List of reporters
            output_dir: Base directory for reports
        """
        self.reporters = reporters
        self.output_dir = output_dir
        self._current_execution: Optional[Execution] = None

    def start_execution(
        self,
        execution_id: Optional[ExecutionId] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Execution:
        """
        Start a new test execution

        Args:
            execution_id: Optional execution ID (generated if not provided)
            metadata: Optional metadata (environment, tags, etc.)

        Returns:
            Execution entity
        """
        # Create execution entity
        self._current_execution = Execution.create(execution_id)

        # Add metadata
        if metadata:
            for key, value in metadata.items():
                self._current_execution.add_metadata(key, value)

        # Notify reporters
        for reporter in self.reporters:
            reporter.start_execution(self._current_execution)

        return self._current_execution

    def add_scenario(self, scenario: Scenario) -> None:
        """
        Add scenario to current execution

        Args:
            scenario: Scenario entity

        Raises:
            ValueError: If no execution is active
        """
        if not self._current_execution:
            raise ValueError("No active execution. Call start_execution() first.")

        self._current_execution.add_scenario(scenario)

    def end_execution(self) -> Execution:
        """
        End current execution and generate reports

        Returns:
            Completed execution entity

        Raises:
            ValueError: If no execution is active
        """
        if not self._current_execution:
            raise ValueError("No active execution to end.")

        # Complete execution
        self._current_execution.complete()

        # Notify reporters
        for reporter in self.reporters:
            reporter.end_execution(self._current_execution)

        # Generate reports using Use Case
        report_use_case = GenerateExecutionReportUseCase(self.reporters)
        execution_dir = self.output_dir / str(self._current_execution.execution_id)
        execution_dir.mkdir(parents=True, exist_ok=True)

        report_paths = report_use_case.execute(self._current_execution, execution_dir)

        # Log report paths
        for path in report_paths:
            print(f"Report generated: {path}")

        return self._current_execution

    def get_current_execution(self) -> Optional[Execution]:
        """Get current execution"""
        return self._current_execution

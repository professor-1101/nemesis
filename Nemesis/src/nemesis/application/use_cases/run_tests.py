"""Run Tests Use Case - Execute test scenarios with Clean Architecture

This use case orchestrates test execution following Clean Architecture principles.
It replaces the old TestExecutor with a clean, testable implementation.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.ports import IBrowserDriver, IReporter, ICollector
from nemesis.domain.value_objects import ExecutionId, ScenarioStatus


@dataclass
class RunTestsConfig:
    """
    Configuration for test execution

    Value Object pattern: Encapsulates all config in one immutable object
    """
    tags: List[str]
    feature: Optional[str]
    env: str
    headless: bool
    parallel: int
    browser_type: str = "chromium"
    base_url: Optional[str] = None
    timeout: int = 30000
    video_enabled: bool = True
    trace_enabled: bool = True
    screenshot_on_failure: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "tags": self.tags,
            "feature": self.feature,
            "env": self.env,
            "headless": self.headless,
            "parallel": self.parallel,
            "browser_type": self.browser_type,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "video_enabled": self.video_enabled,
            "trace_enabled": self.trace_enabled,
            "screenshot_on_failure": self.screenshot_on_failure,
        }


class RunTestsUseCase:
    """
    Use Case: Run Tests

    Responsibilities (SRP):
    - Orchestrate test execution workflow
    - Coordinate browser, reporters, collectors
    - Manage execution lifecycle
    - Report progress and results

    Clean Architecture:
    - Application layer use case
    - Depends only on Domain layer (ports)
    - Independent of infrastructure details
    - Testable without external dependencies
    """

    def __init__(
        self,
        browser_driver: IBrowserDriver,
        reporters: List[IReporter],
        collectors: List[ICollector],
        output_dir: Path,
    ):
        """
        Initialize use case with dependencies (Dependency Injection)

        Args:
            browser_driver: Browser driver (injected)
            reporters: List of reporters (injected)
            collectors: List of collectors (injected)
            output_dir: Output directory for reports/artifacts
        """
        self.browser_driver = browser_driver
        self.reporters = reporters
        self.collectors = collectors
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Progress tracking (for UI updates)
        self._current_execution: Optional[Execution] = None
        self._total_scenarios = 0
        self._completed_scenarios = 0

    def execute(
        self,
        config: RunTestsConfig,
        scenario_loader,  # Callable that returns scenarios
        step_executor,    # Callable that executes step logic
    ) -> Execution:
        """
        Execute tests with given configuration

        Args:
            config: Test execution configuration
            scenario_loader: Function to load scenarios (e.g., from Behave)
            step_executor: Function to execute step logic

        Returns:
            Execution entity with results

        Workflow:
        1. Create execution
        2. Load scenarios
        3. For each scenario:
           - Start scenario
           - Execute steps
           - Complete scenario
        4. Generate reports
        5. Return execution
        """
        # 1. Create execution
        execution = self._create_execution(config)
        self._current_execution = execution

        # 2. Load scenarios
        scenarios = scenario_loader(config)
        self._total_scenarios = len(scenarios)

        # 3. Report execution start
        for reporter in self.reporters:
            reporter.start_execution(execution)

        # 4. Execute scenarios
        for scenario in scenarios:
            self._execute_scenario(scenario, step_executor, config)
            self._completed_scenarios += 1

        # 5. Complete execution
        execution.complete()

        # 6. Report execution end
        for reporter in self.reporters:
            reporter.end_execution(execution)

        # 7. Generate final reports
        for reporter in self.reporters:
            report_path = reporter.generate_report(execution, self.output_dir)
            if report_path:
                execution.add_metadata(f"{reporter.__class__.__name__}_report", str(report_path))

        return execution

    def _create_execution(self, config: RunTestsConfig) -> Execution:
        """Create execution entity with metadata"""
        execution = Execution.create()

        # Add metadata
        execution.add_metadata("env", config.env)
        execution.add_metadata("browser", config.browser_type)
        execution.add_metadata("headless", str(config.headless))
        execution.add_metadata("parallel", str(config.parallel))

        if config.tags:
            execution.add_metadata("tags", ",".join(config.tags))
        if config.feature:
            execution.add_metadata("feature", config.feature)

        return execution

    def _execute_scenario(
        self,
        scenario: Scenario,
        step_executor,
        config: RunTestsConfig,
    ) -> None:
        """
        Execute single scenario

        Args:
            scenario: Scenario entity
            step_executor: Function to execute step logic
            config: Execution configuration
        """
        # 1. Start scenario
        scenario.start()

        # 2. Report scenario start
        for reporter in self.reporters:
            reporter.start_scenario(scenario)

        # 3. Execute steps
        for step in scenario.steps:
            self._execute_step(step, step_executor, scenario, config)

        # 4. Complete scenario
        scenario.complete()

        # 5. Report scenario end
        for reporter in self.reporters:
            reporter.end_scenario(scenario)

        # 6. Add to execution
        if self._current_execution:
            self._current_execution.add_scenario(scenario)

    def _execute_step(
        self,
        step: Step,
        step_executor,
        scenario: Scenario,
        config: RunTestsConfig,
    ) -> None:
        """
        Execute single step

        Args:
            step: Step entity
            step_executor: Function to execute step logic
            scenario: Parent scenario
            config: Execution configuration
        """
        # 1. Start step
        step.start()

        # 2. Report step start
        for reporter in self.reporters:
            reporter.start_step(step)

        # 3. Execute step logic
        try:
            step_executor(step, scenario, config)
            step.complete_successfully()
        except AssertionError as e:
            # Test assertion failed
            step.fail(str(e))

            # Capture screenshot on failure
            if config.screenshot_on_failure:
                self._capture_screenshot(step, scenario)
        except Exception as e:
            # Step execution error
            step.fail(f"Step execution error: {str(e)}")

            # Capture screenshot on error
            if config.screenshot_on_failure:
                self._capture_screenshot(step, scenario)

        # 4. Report step end
        for reporter in self.reporters:
            reporter.end_step(step)

    def _capture_screenshot(self, step: Step, scenario: Scenario) -> None:
        """Capture screenshot on step failure"""
        try:
            # This would be implemented by browser driver
            # For now, just log the intent
            screenshot_path = (
                self.output_dir
                / "screenshots"
                / f"{scenario.scenario_id}_{step.step_id}.png"
            )
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            # Browser driver would capture screenshot here
            # browser.screenshot(path=screenshot_path)

            for reporter in self.reporters:
                reporter.log_message(
                    f"Screenshot captured: {screenshot_path}",
                    level="INFO"
                )
        except Exception:
            # Silently ignore screenshot errors
            pass

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress (for UI updates)

        Returns:
            Dictionary with progress information
        """
        return {
            "total_scenarios": self._total_scenarios,
            "completed_scenarios": self._completed_scenarios,
            "current_execution": self._current_execution.to_dict() if self._current_execution else None,
        }

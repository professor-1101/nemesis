"""Execute Test Scenario Use Case

This use case orchestrates the execution of a single test scenario.
It coordinates browser setup, step execution, and result collection.
"""

from typing import List, Callable
from pathlib import Path

from nemesis.domain.entities import Scenario, Step
from nemesis.domain.ports import IBrowserDriver, IReporter, ICollector


class ExecuteTestScenarioUseCase:
    """
    Use Case: Execute Test Scenario

    Responsibilities:
    - Create browser session
    - Execute scenario steps
    - Collect data (console, network, performance)
    - Report results
    - Handle failures gracefully

    Clean Architecture:
    - Depends on Domain (Scenario, Step)
    - Depends on Ports (interfaces), not implementations
    - Infrastructure-agnostic business logic
    """

    def __init__(
        self,
        browser_driver: IBrowserDriver,
        reporters: List[IReporter],
        collectors: List[ICollector],
    ):
        """
        Initialize use case with dependencies (Dependency Injection)

        Args:
            browser_driver: Browser automation driver (interface)
            reporters: List of reporters (interfaces)
            collectors: List of data collectors (interfaces)
        """
        self.browser_driver = browser_driver
        self.reporters = reporters
        self.collectors = collectors

    def execute(
        self,
        scenario: Scenario,
        step_executor: Callable[[Step], None],
    ) -> Scenario:
        """
        Execute a test scenario

        Args:
            scenario: Scenario entity to execute
            step_executor: Function to execute each step (from test code)

        Returns:
            Updated scenario with results

        Raises:
            Various exceptions from browser/step execution
        """
        # 1. Report scenario start
        for reporter in self.reporters:
            reporter.start_scenario(scenario)

        # 2. Start scenario execution
        scenario.start()

        # 3. Start collectors
        for collector in self.collectors:
            collector.start()

        try:
            # 4. Execute each step
            for step in scenario.steps:
                self._execute_step(step, step_executor)

            # 5. Complete scenario (status calculated from steps)
            scenario.complete()

        except Exception as e:
            # Handle scenario-level failure
            scenario.fail(str(e))
            raise

        finally:
            # 6. Stop collectors
            for collector in self.collectors:
                collector.stop()

            # 7. Report scenario end
            for reporter in self.reporters:
                reporter.end_scenario(scenario)

        return scenario

    def _execute_step(self, step: Step, step_executor: Callable[[Step], None]) -> None:
        """
        Execute a single step

        Args:
            step: Step entity
            step_executor: Function to execute step logic
        """
        # Report step start
        for reporter in self.reporters:
            reporter.start_step(step)

        # Start step
        step.start()

        try:
            # Execute step logic (provided by test code)
            step_executor(step)

            # Mark as successful
            step.complete_successfully()

        except AssertionError as e:
            # Assertion failure
            step.fail(f"Assertion failed: {e}")
            raise

        except Exception as e:
            # Other failure
            step.fail(f"Error: {e}")
            raise

        finally:
            # Report step end
            for reporter in self.reporters:
                reporter.end_step(step)

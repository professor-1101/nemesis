"""Scenario Coordinator - Manages scenario execution"""

from typing import Callable, List, Optional

from nemesis.domain.entities import Scenario, Step
from nemesis.domain.ports import IBrowserDriver, IReporter, ICollector, ILogger
from nemesis.application.use_cases import ExecuteTestScenarioUseCase


class ScenarioCoordinator:
    """
    Application Service: Scenario Coordinator

    Responsibilities (SRP):
    - Coordinate scenario execution
    - Manage browser session for scenario
    - Collect scenario artifacts
    - Handle scenario failures

    This replaces scenario-related logic from old god classes.
    """

    def __init__(
        self,
        browser_driver: IBrowserDriver,
        reporters: List[IReporter],
        collectors: List[ICollector],
        logger: ILogger,
    ):
        """
        Initialize coordinator

        Args:
            browser_driver: Browser driver (Dependency Injection)
            reporters: List of reporters
            collectors: List of collectors
            logger: Logger implementation (Dependency Injection)
        """
        self.browser_driver = browser_driver
        self.reporters = reporters
        self.collectors = collectors
        self.logger = logger

    def execute_scenario(
        self,
        scenario: Scenario,
        step_executor: Callable[[Step], None],
    ) -> Scenario:
        """
        Execute a scenario with all steps

        Args:
            scenario: Scenario entity
            step_executor: Function to execute step logic

        Returns:
            Updated scenario with results
        """
        # Use ExecuteTestScenarioUseCase
        use_case = ExecuteTestScenarioUseCase(
            self.browser_driver,
            self.reporters,
            self.collectors,
        )

        return use_case.execute(scenario, step_executor)

    def collect_artifacts(self, output_dir) -> dict:
        """
        Collect all artifacts from collectors

        Args:
            output_dir: Directory to save artifacts

        Returns:
            Dictionary of artifact paths by type
        """
        artifacts = {}

        for collector in self.collectors:
            try:
                # Get collector name
                collector_name = collector.__class__.__name__.replace("Collector", "").lower()

                # Save collector data
                output_path = output_dir / f"{collector_name}.json"
                collector.save_to_file(output_path)

                artifacts[collector_name] = output_path

            except Exception as e:
                self.logger.warning(f"Failed to collect from {collector.__class__.__name__}: {e}")

        return artifacts

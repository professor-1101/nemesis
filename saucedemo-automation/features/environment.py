"""Refactored Behave environment using Nemesis Clean Architecture.

This environment file demonstrates the new Clean Architecture approach:
- Dependency Injection via Composition Root
- Domain-driven design with Ports & Adapters
- Framework independence through abstractions
- Clean separation of concerns
"""

from pathlib import Path
from typing import List, Optional

from behave.runner import Context

# Domain Layer - Value Objects & Entities
from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import ExecutionId, ScenarioStatus, StepStatus
from nemesis.domain.ports import IBrowserDriver, IReporter, IPage

# Application Layer - Use Cases & Coordinators
from nemesis.application.services import ExecutionCoordinator, ScenarioCoordinator
from nemesis.application.use_cases import ExecuteTestScenarioUseCase

# Infrastructure Layer - Adapters
from nemesis.infrastructure.browser import PlaywrightBrowserDriver
from nemesis.infrastructure.reporting import JSONReporter, ConsoleReporter


class DependencyContainer:
    """
    Composition Root: Single place for dependency injection.

    This is the ONLY place where we wire up concrete implementations.
    All other code depends on abstractions (interfaces).
    """

    def __init__(self, config: dict):
        self.config = config
        self.output_dir = Path(config.get("output_dir", "./reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Infrastructure: Browser Driver
        # Note: Browser type is set during launch, not in constructor
        self.browser_driver = PlaywrightBrowserDriver()

        # Infrastructure: Reporters
        self.reporters: List[IReporter] = [
            ConsoleReporter(),  # Cypress-like CLI output
            JSONReporter(output_dir=self.output_dir),  # JSON reports
        ]

        # Application: Coordinators
        self.execution_coordinator = ExecutionCoordinator(
            reporters=self.reporters,
            output_dir=self.output_dir
        )

        self.scenario_coordinator = ScenarioCoordinator(
            browser_driver=self.browser_driver,
            reporters=self.reporters,
            collectors=[]  # No collectors for now
        )

        # Domain entities (created during execution)
        self.current_execution: Optional[Execution] = None
        self.current_scenario: Optional[Scenario] = None
        self.browser = None
        self.page = None

    def start_execution(self) -> Execution:
        """Start a new test execution."""
        self.current_execution = self.execution_coordinator.start_execution()
        return self.current_execution

    def end_execution(self) -> None:
        """End the current test execution."""
        if self.current_execution:
            self.execution_coordinator.end_execution()

    def launch_browser(self, headless: bool = False) -> None:
        """Launch browser."""
        self.browser = self.browser_driver.launch(headless=headless)
        self.page = self.browser.new_page()

    def close_browser(self) -> None:
        """Close browser and cleanup."""
        if self.browser:
            self.browser.close()
        if self.browser_driver:
            self.browser_driver.close()

    def start_scenario(self, scenario_name: str, feature_name: str) -> Scenario:
        """Start a new scenario."""
        scenario = Scenario.create(
            name=scenario_name,
            feature_name=feature_name
        )

        # Report scenario start
        for reporter in self.reporters:
            reporter.start_scenario(scenario)

        scenario.start()
        self.current_scenario = scenario

        # Add to execution
        if self.current_execution:
            self.current_execution.add_scenario(scenario)

        return scenario

    def end_scenario(self) -> None:
        """End the current scenario."""
        if self.current_scenario:
            self.current_scenario.complete()

            # Report scenario end
            for reporter in self.reporters:
                reporter.end_scenario(self.current_scenario)


# ============================================================================
# BEHAVE HOOKS
# ============================================================================

def before_all(context: Context) -> None:
    """
    Initialize framework before all tests.

    This is the Composition Root where we wire up all dependencies.
    """
    # Load configuration
    config = {
        "browser_type": context.config.userdata.get("browser", "chromium"),
        "headless": context.config.userdata.get("headless", "false").lower() == "true",
        "output_dir": context.config.userdata.get("output_dir", "./reports"),
        "base_url": "https://www.saucedemo.com",
    }

    # Create dependency container
    context.container = DependencyContainer(config)
    context.config_data = config

    # Start execution
    context.execution = context.container.start_execution()

    print(f"\n[SauceDemo] Execution started: {context.execution.execution_id.value}")


def after_all(context: Context) -> None:
    """
    Cleanup after all tests complete.
    """
    # End execution and generate reports
    context.container.end_execution()

    print(f"\n[SauceDemo] Execution completed")
    print(f"  Total: {context.execution.get_total_scenarios_count()}")
    print(f"  Passed: {context.execution.get_passed_scenarios_count()}")
    print(f"  Failed: {context.execution.get_failed_scenarios_count()}")


def before_feature(context: Context, feature) -> None:
    """
    Setup before each feature.
    """
    context.feature_name = feature.name


def after_feature(context: Context, feature) -> None:
    """
    Cleanup after each feature.
    """
    pass


def before_scenario(context: Context, scenario) -> None:
    """
    Setup before each scenario.

    Clean Architecture approach:
    - Launch browser using IBrowserDriver abstraction
    - Create Scenario entity
    - Use dependency injection
    """
    # Launch browser
    headless = context.config_data.get("headless", False)
    context.container.launch_browser(headless=headless)

    # Make browser page available to steps
    context.page = context.container.page
    # Note: cannot use 'config' as attribute name (reserved by behave)
    context.test_config = context.config_data

    # Start scenario
    context.scenario_entity = context.container.start_scenario(
        scenario_name=scenario.name,
        feature_name=context.feature_name
    )


def after_scenario(context: Context, scenario) -> None:
    """
    Cleanup after each scenario.
    """
    # Handle scenario failure
    if scenario.status == "failed":
        if context.container.current_scenario:
            context.container.current_scenario.fail(f"Scenario failed: {scenario.name}")

    # End scenario
    context.container.end_scenario()

    # Close browser
    context.container.close_browser()


def before_step(context: Context, step) -> None:
    """
    Setup before each step.
    """
    # Create step entity
    step_entity = Step.create(
        keyword=step.keyword,
        name=step.name
    )
    step_entity.start()

    # Add to current scenario
    if context.container.current_scenario:
        context.container.current_scenario.add_step(step_entity)

    context.current_step = step_entity

    # Report step start
    for reporter in context.container.reporters:
        reporter.start_step(step_entity)


def after_step(context: Context, step) -> None:
    """
    Cleanup after each step.
    """
    if hasattr(context, 'current_step'):
        # Mark step as completed or failed
        if step.status == "failed":
            error_msg = str(step.exception) if step.exception else "Step failed"
            context.current_step.fail(error_msg)
        else:
            context.current_step.complete_successfully()

        # Report step end
        for reporter in context.container.reporters:
            reporter.end_step(context.current_step)

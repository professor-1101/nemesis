"""Scenario-level hooks for Nemesis framework."""
import traceback
from typing import Any

from nemesis.infrastructure.logging import Logger


LOGGER = Logger.get_instance({})


def before_scenario(context: Any, scenario: Any) -> None:
    """Before each scenario.

    Args:
        context: Behave context object
        scenario: Behave scenario object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_manager import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

        env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

        # Check if browser already crashed
        if hasattr(context, 'browser_crashed') and context.browser_crashed:
            LOGGER.warning(f"Browser already crashed, skipping scenario: {scenario.name}")
            scenario.skip("Browser crashed in previous scenario")
            return

        # LAZY BROWSER INITIALIZATION: Don't start browser here
        # Browser will be started on-demand in before_step when actually needed
        # This prevents interference with Behave step discovery

        # Initialize browser manager reference (but don't start browser)
        if not hasattr(context, 'browser_manager'):
            context.browser_manager = env_manager.browser_env.get_browser_manager()

        # Mark browser as not started yet (lazy initialization)
        context.browser_started = False
        context.browser_crashed = False

        # Start scenario reporting
        env_manager.reporting_env.start_scenario(context, scenario)

        # Log scenario start
        env_manager.logger_env.log_scenario_start(context, scenario)

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Scenario setup errors
        LOGGER.error(f"Error in before_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="before_scenario")
        context.browser_crashed = True
        if hasattr(scenario, 'skip'):
            scenario.skip(f"Setup failed: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.error(f"Error in before_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="before_scenario")
        context.browser_crashed = True
        if hasattr(scenario, 'skip'):
            scenario.skip(f"Setup failed: {e}")


def after_scenario(context: Any, scenario: Any) -> None:
    """After each scenario.

    Args:
        context: Behave context object
        scenario: Behave scenario object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_manager import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

        env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

        # Determine scenario status
        status = "passed"
        if scenario.status == 'failed':
            status = "failed"
            context.test_failed = True

        # Check if browser crashed during scenario
        if hasattr(context, 'browser_crashed') and context.browser_crashed:
            status = "failed"
            context.test_failed = True
            LOGGER.warning(f"Browser crashed during scenario: {scenario.name}")

        # Stop browser for scenario (graceful - only if started)
        env_manager.browser_env.stop_browser_for_scenario(context, scenario, status)

        # End scenario reporting
        env_manager.reporting_env.end_scenario(context, scenario, status)

        # Log scenario end
        env_manager.logger_env.log_scenario_end(context, scenario, status)

        LOGGER.info(f"Scenario completed: {scenario.name} (status: {status})")

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Scenario teardown errors - log but continue
        LOGGER.warning(f"Error in after_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="after_scenario")
        # Don't mark browser as crashed here - scenario is ending anyway
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="after_scenario")
        # Don't mark browser as crashed here - scenario is ending anyway

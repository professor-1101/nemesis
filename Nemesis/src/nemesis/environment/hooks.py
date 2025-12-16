"""Behave hooks for Nemesis framework."""
import traceback
from typing import Any, TYPE_CHECKING

from nemesis.core.logging import Logger

# Lazy import to break cyclic dependency:
# hooks -> environment_manager -> reporting_environment -> reporting.manager ->
# reporting.management.reporter_manager -> hooks (cyclic!)
if TYPE_CHECKING:
    from .environment_manager import EnvironmentManager

LOGGER = Logger.get_instance({})


# Global environment manager instance
_env_manager: Any = None


def _get_env_manager() -> Any:
    """Get or create environment manager instance.
    
    Returns:
        EnvironmentManager instance
    """
    global _env_manager
    if _env_manager is None:
        # Lazy import to avoid cyclic dependency at module load time
        from .environment_manager import EnvironmentManager  # pylint: disable=import-outside-toplevel
        _env_manager = EnvironmentManager()
    return _env_manager


def before_all(context: Any) -> None:
    """Initialize framework before all tests.

    Args:
        context: Behave context object
    """
    try:
        print("Starting Nemesis test suite...")

        # Setup environment
        env_manager = _get_env_manager()
        success = env_manager.setup_environment(context)

        if not success:
            print("Environment setup failed, but continuing...")
        else:
            print("Environment setup completed successfully")

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError, ImportError) as e:
        # Environment setup errors
        LOGGER.error(f"Critical error in before_all: {e}", traceback=traceback.format_exc(), module=__name__, function="before_all")
        print(f"Critical error in before_all: {e}")
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment setup
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.error(f"Critical error in before_all: {e}", traceback=traceback.format_exc(), module=__name__, function="before_all")
        print(f"Critical error in before_all: {e}")
        raise


def after_all(context: Any) -> None:
    """Cleanup after all tests.

    Args:
        context: Behave context object
    """
    try:
        print("Ending Nemesis test suite...")

        # Determine final status
        status = "completed"
        if hasattr(context, 'test_failed') and context.test_failed:
            status = "failed"

        # Teardown environment
        env_manager = _get_env_manager()
        env_manager.teardown_environment(context, status)

        print(f"Test suite completed with status: {status}")

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Environment teardown errors - log but don't fail
        LOGGER.warning(f"Error in after_all: {e}", traceback=traceback.format_exc(), module=__name__, function="after_all")
        print(f"Error in after_all: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment teardown
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_all: {e}", traceback=traceback.format_exc(), module=__name__, function="after_all")
        print(f"Error in after_all: {e}")


def before_feature(context: Any, feature: Any) -> None:
    """Before each feature.

    Args:
        context: Behave context object
        feature: Behave feature object
    """
    try:
        env_manager = _get_env_manager()

        # Start feature reporting
        env_manager.reporting_env.start_feature(context, feature)

        # Log feature start
        env_manager.logger_env.log_feature_start(context, feature)

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Feature setup errors - log but continue
        LOGGER.warning(f"Error in before_feature: {e}", traceback=traceback.format_exc(), module=__name__, function="before_feature")
        print(f"Error in before_feature: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or reporting
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in before_feature: {e}", traceback=traceback.format_exc(), module=__name__, function="before_feature")
        print(f"Error in before_feature: {e}")


def after_feature(context: Any, feature: Any) -> None:
    """After each feature.

    Args:
        context: Behave context object
        feature: Behave feature object
    """
    try:
        env_manager = _get_env_manager()

        # Determine feature status
        status = "passed"
        if hasattr(feature, 'status') and feature.status == 'failed':
            status = "failed"

        # End feature reporting
        env_manager.reporting_env.end_feature(context, feature, status)

        # Log feature end
        env_manager.logger_env.log_feature_end(context, feature, status)

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Feature teardown errors - log but continue
        LOGGER.warning(f"Error in after_feature: {e}", traceback=traceback.format_exc(), module=__name__, function="after_feature")
        print(f"Error in after_feature: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or reporting
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_feature: {e}", traceback=traceback.format_exc(), module=__name__, function="after_feature")
        print(f"Error in after_feature: {e}")


def before_scenario(context: Any, scenario: Any) -> None:
    """Before each scenario.

    Args:
        context: Behave context object
        scenario: Behave scenario object
    """
    try:
        env_manager = _get_env_manager()

        # Check if browser already crashed
        if hasattr(context, 'browser_crashed') and context.browser_crashed:
            print(f"Browser already crashed, skipping scenario: {scenario.name}")
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
        print(f"Error in before_scenario: {e}")
        context.browser_crashed = True
        if hasattr(scenario, 'skip'):
            scenario.skip(f"Setup failed: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.error(f"Error in before_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="before_scenario")
        print(f"Error in before_scenario: {e}")
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
        env_manager = _get_env_manager()

        # Determine scenario status
        status = "passed"
        if scenario.status == 'failed':
            status = "failed"
            context.test_failed = True

        # Check if browser crashed during scenario
        if hasattr(context, 'browser_crashed') and context.browser_crashed:
            status = "failed"
            context.test_failed = True
            print(f"Browser crashed during scenario: {scenario.name}")

        # Stop browser for scenario (graceful - only if started)
        env_manager.browser_env.stop_browser_for_scenario(context, scenario, status)

        # End scenario reporting
        env_manager.reporting_env.end_scenario(context, scenario, status)

        # Log scenario end
        env_manager.logger_env.log_scenario_end(context, scenario, status)

        print(f"Scenario completed: {scenario.name} (status: {status})")

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Scenario teardown errors - log but continue
        LOGGER.warning(f"Error in after_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="after_scenario")
        print(f"Error in after_scenario: {e}")
        # Don't mark browser as crashed here - scenario is ending anyway
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_scenario: {e}", traceback=traceback.format_exc(), module=__name__, function="after_scenario")
        print(f"Error in after_scenario: {e}")
        # Don't mark browser as crashed here - scenario is ending anyway


def before_step(context: Any, step: Any) -> None:
    """Before each step.

    Args:
        context: Behave context object
        step: Behave step object
    """
    try:
        env_manager = _get_env_manager()

        # LAZY BROWSER STARTUP: Start browser on-demand when first step runs
        if not getattr(context, 'browser_started', False) and not getattr(context, 'browser_crashed', False):
            try:
                print(f"Starting browser for step: {step.step_type} {step.name}")
                browser_started = env_manager.browser_env.start_browser_for_scenario(context, step)
                if browser_started:
                    context.browser_started = True
                    print("Browser started successfully")
                else:
                    print("Failed to start browser, marking as crashed")
                    context.browser_crashed = True
            except (AttributeError, RuntimeError) as e:
                # Browser startup errors
                LOGGER.error(f"Browser startup failed: {e}", traceback=traceback.format_exc(), module=__name__, function="before_step")
                print(f"Browser startup failed: {e}")
                context.browser_crashed = True
            except (KeyboardInterrupt, SystemExit):
                # Always re-raise these to allow proper program termination
                raise

        # Start step reporting
        env_manager.reporting_env.start_step(context, step)

        # Log step start
        env_manager.logger_env.log_step_start(context, step)

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Step setup errors - log but continue
        LOGGER.warning(f"Error in before_step: {e}", traceback=traceback.format_exc(), module=__name__, function="before_step")
        print(f"Error in before_step: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in before_step: {e}", traceback=traceback.format_exc(), module=__name__, function="before_step")
        print(f"Error in before_step: {e}")


def after_step(context: Any, step: Any) -> None:
    """After each step.

    Args:
        context: Behave context object
        step: Behave step object
    """
    try:
        env_manager = _get_env_manager()

        # Determine step status
        status = "passed"
        if step.status == 'failed':
            status = "failed"

        # End step reporting
        env_manager.reporting_env.end_step(context, step, status)

        # Log step end
        env_manager.logger_env.log_step_end(context, step, status)

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Step teardown errors - log but continue
        LOGGER.warning(f"Error in after_step: {e}", traceback=traceback.format_exc(), module=__name__, function="after_step")
        print(f"Error in after_step: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_step: {e}", traceback=traceback.format_exc(), module=__name__, function="after_step")
        print(f"Error in after_step: {e}")

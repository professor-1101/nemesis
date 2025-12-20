"""Scenario-level hooks for Nemesis framework."""
import traceback
from typing import Any

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


LOGGER = Logger.get_instance({})


def _setup_action_logging_for_scenario(env_manager, context, scenario) -> None:
    """Setup action logging for the current scenario"""
    try:
        # Get current page adapter from browser environment
        if hasattr(env_manager, 'browser_env') and env_manager.browser_env:
            browser_env = env_manager.browser_env
            if hasattr(browser_env, '_current_page_adapter') and browser_env._current_page_adapter:
                page_adapter = browser_env._current_page_adapter

                # Create action logger callback that logs to ReportPortal
                def action_logger_callback(message: str) -> None:
                    try:
                        # Log to ReportPortal for this scenario
                        if hasattr(env_manager, 'reporting_env') and env_manager.reporting_env:
                            reporting_env = env_manager.reporting_env
                            if hasattr(reporting_env, '_reporter_manager') and reporting_env._reporter_manager:
                                reporter_manager = reporting_env._reporter_manager
                                if reporter_manager.is_rp_enabled():
                                    rp_client = reporter_manager.get_rp_client()
                                    if rp_client:
                                        rp_client.log_message(message, "DEBUG")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        LOGGER.warning(f"Failed to log action to ReportPortal: {e}")

                # Set the action logger on the page adapter
                page_adapter.set_action_logger(action_logger_callback)
                LOGGER.debug(f"Action logging enabled for scenario: {scenario.name}")

    except Exception as e:  # pylint: disable=broad-exception-caught
        LOGGER.warning(f"Failed to setup action logging: {e}")


def before_scenario(context: Any, scenario: Any) -> None:
    """Before each scenario.

    Args:
        context: Behave context object
        scenario: Behave scenario object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_coordinator import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

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
        
        # Set test_config for page objects (cannot use 'config' as it's reserved by behave)
        if not hasattr(context, 'test_config'):
            config_dict = env_manager.config.load()
            context.test_config = {
                "base_url": config_dict.get("environments", {}).get("dev", {}).get("base_url", "https://www.saucedemo.com"),
                "browser_type": config_dict.get("browser", {}).get("type", "chromium"),
                "headless": config_dict.get("browser", {}).get("headless", False),
            }

        # Start scenario reporting
        env_manager.reporting_env.start_scenario(context, scenario)

        # Clear previous scenario actions and setup action logging
        env_manager.clear_scenario_actions()
        _setup_action_logging_for_scenario(env_manager, context, scenario)

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


@handle_exceptions_with_fallback(
    logger=LOGGER,
    log_level="warning",
    specific_exceptions=(AttributeError, RuntimeError),
    specific_message="Error in after_scenario: {error}",
    fallback_message="Error in after_scenario: {error}"
)
def after_scenario(context: Any, scenario: Any) -> None:
    """After each scenario.

    Args:
        context: Behave context object
        scenario: Behave scenario object
    """
    # Lazy import to avoid circular dependency
    from .environment_coordinator import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

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

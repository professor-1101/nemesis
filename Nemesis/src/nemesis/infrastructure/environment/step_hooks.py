"""Step-level hooks for Nemesis framework."""
import traceback
from typing import Any

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


LOGGER = Logger.get_instance({})


def _setup_action_logging_after_browser_start(env_manager, context, step) -> None:
    """Setup action logging for Playwright after browser starts"""
    try:
        # Get current page adapter from context (should be set by browser_environment)
        if hasattr(context, 'page') and context.page:
            page_adapter = context.page
            LOGGER.info(f"Found page adapter in context: {type(page_adapter)}")

            # Create action logger callback that logs to ReportPortal
            def action_logger_callback(message: str) -> None:
                try:
                    LOGGER.debug(f"Action callback called: {message}")

                    # Add action to scenario's action list for stack trace
                    env_manager.add_scenario_action(message)

                    # Add action to current step's action list for step-level stack trace
                    env_manager.add_step_action(message)

                    # Log to ReportPortal for the current active item (scenario/test/step)
                    if hasattr(env_manager, 'reporting_env') and env_manager.reporting_env:
                        reporting_env = env_manager.reporting_env
                        if hasattr(reporting_env, '_reporter_manager') and reporting_env._reporter_manager:
                            reporter_manager = reporting_env._reporter_manager
                            if reporter_manager.is_rp_enabled():
                                rp_client = reporter_manager.get_rp_client()
                                if rp_client:
                                    rp_client.log_message(message, "DEBUG")
                                    LOGGER.debug(f"Logged action to RP: {message}")
                                else:
                                    LOGGER.warning("RP client not available")
                            else:
                                LOGGER.warning("RP not enabled")
                        else:
                            LOGGER.warning("Reporter manager not available")
                    else:
                        LOGGER.warning("Reporting env not available")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    LOGGER.warning(f"Failed to log action to ReportPortal: {e}")

            # Set the action logger on the page adapter
            page_adapter.set_action_logger(action_logger_callback)
            LOGGER.info(f"Action logging enabled for step: {step.name}")

        else:
            LOGGER.warning("Page adapter not found in context")

    except Exception as e:  # pylint: disable=broad-exception-caught
        LOGGER.warning(f"Failed to setup action logging: {e}")


@handle_exceptions_with_fallback(
    logger=LOGGER,
    log_level="warning",
    specific_exceptions=(AttributeError, RuntimeError),
    specific_message="Error in before_step: {error}",
    fallback_message="Error in before_step: {error}"
)
def before_step(context: Any, step: Any) -> None:
    """Before each step.

    Args:
        context: Behave context object
        step: Behave step object
    """
    # Lazy import to avoid circular dependency
    from .environment_coordinator import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

    env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

    # LAZY BROWSER STARTUP: Start browser on-demand when first step runs
    if not getattr(context, 'browser_started', False) and not getattr(context, 'browser_crashed', False):
        try:
            LOGGER.info(f"Starting browser for step: {step.step_type} {step.name}")
            browser_started = env_manager.browser_env.start_browser_for_scenario(context, step)
            if browser_started:
                context.browser_started = True
                LOGGER.info("Browser started successfully")

                # Setup action logging for Playwright after browser starts
                try:
                    _setup_action_logging_after_browser_start(env_manager, context, step)
                    LOGGER.info("Action logging setup completed")
                except Exception as e:
                    LOGGER.error(f"Failed to setup action logging: {e}", traceback=traceback.format_exc())
            else:
                LOGGER.error("Failed to start browser, marking as crashed")
                context.browser_crashed = True
        except (AttributeError, RuntimeError) as e:
            # Browser startup errors
            LOGGER.error(f"Browser startup failed: {e}", traceback=traceback.format_exc(), module=__name__, function="before_step")
            context.browser_crashed = True
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise

    # Start step reporting
    env_manager.reporting_env.start_step(context, step)

    # Clear previous step actions for step-level stack trace
    env_manager.clear_step_actions()

    # Log step start
    env_manager.logger_env.log_step_start(context, step)


@handle_exceptions_with_fallback(
    logger=LOGGER,
    log_level="warning",
    specific_exceptions=(AttributeError, RuntimeError),
    specific_message="Error in after_step: {error}",
    fallback_message="Error in after_step: {error}"
)
def after_step(context: Any, step: Any) -> None:
    """After each step.

    Args:
        context: Behave context object
        step: Behave step object
    """
    # Lazy import to avoid circular dependency
    from .environment_coordinator import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

    env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

    # Determine step status
    status = "passed"
    if step.status == 'failed':
        status = "failed"

    # End step reporting
    env_manager.reporting_env.end_step(context, step, status)

    # Log step end
    env_manager.logger_env.log_step_end(context, step, status)

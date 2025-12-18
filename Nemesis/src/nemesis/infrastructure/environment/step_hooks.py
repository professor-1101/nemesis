"""Step-level hooks for Nemesis framework."""
import traceback
from typing import Any

from nemesis.infrastructure.logging import Logger


LOGGER = Logger.get_instance({})


def before_step(context: Any, step: Any) -> None:
    """Before each step.

    Args:
        context: Behave context object
        step: Behave step object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_manager import EnvironmentManager  # pylint: disable=import-outside-toplevel

        env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentManager()

        # LAZY BROWSER STARTUP: Start browser on-demand when first step runs
        if not getattr(context, 'browser_started', False) and not getattr(context, 'browser_crashed', False):
            try:
                LOGGER.info(f"Starting browser for step: {step.step_type} {step.name}")
                browser_started = env_manager.browser_env.start_browser_for_scenario(context, step)
                if browser_started:
                    context.browser_started = True
                    LOGGER.info("Browser started successfully")
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

        # Log step start
        env_manager.logger_env.log_step_start(context, step)

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Step setup errors - log but continue
        LOGGER.warning(f"Error in before_step: {e}", traceback=traceback.format_exc(), module=__name__, function="before_step")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in before_step: {e}", traceback=traceback.format_exc(), module=__name__, function="before_step")


def after_step(context: Any, step: Any) -> None:
    """After each step.

    Args:
        context: Behave context object
        step: Behave step object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_manager import EnvironmentManager  # pylint: disable=import-outside-toplevel

        env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentManager()

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
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_step: {e}", traceback=traceback.format_exc(), module=__name__, function="after_step")

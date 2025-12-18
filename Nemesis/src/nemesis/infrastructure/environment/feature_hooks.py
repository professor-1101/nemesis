"""Feature-level hooks for Nemesis framework."""
import traceback
from typing import Any

from nemesis.infrastructure.logging import Logger


LOGGER = Logger.get_instance({})


def before_feature(context: Any, feature: Any) -> None:
    """Before each feature.

    Args:
        context: Behave context object
        feature: Behave feature object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_manager import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

        env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

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
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or reporting
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in before_feature: {e}", traceback=traceback.format_exc(), module=__name__, function="before_feature")


def after_feature(context: Any, feature: Any) -> None:
    """After each feature.

    Args:
        context: Behave context object
        feature: Behave feature object
    """
    try:
        # Lazy import to avoid circular dependency
        from .environment_manager import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

        env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

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
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or reporting
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_feature: {e}", traceback=traceback.format_exc(), module=__name__, function="after_feature")

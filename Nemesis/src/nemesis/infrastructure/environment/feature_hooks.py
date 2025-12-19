"""Feature-level hooks for Nemesis framework."""
from typing import Any

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


LOGGER = Logger.get_instance({})


@handle_exceptions_with_fallback(
    logger=LOGGER,
    log_level="warning",
    specific_exceptions=(AttributeError, RuntimeError),
    specific_message="Error in before_feature: {error}",
    fallback_message="Error in before_feature: {error}"
)
def before_feature(context: Any, feature: Any) -> None:
    """Before each feature.

    Args:
        context: Behave context object
        feature: Behave feature object
    """
    # Lazy import to avoid circular dependency
    from .environment_manager import EnvironmentCoordinator  # pylint: disable=import-outside-toplevel

    env_manager = context.env_manager if hasattr(context, 'env_manager') else EnvironmentCoordinator()

    # Start feature reporting
    env_manager.reporting_env.start_feature(context, feature)

    # Log feature start
    env_manager.logger_env.log_feature_start(context, feature)


@handle_exceptions_with_fallback(
    logger=LOGGER,
    log_level="warning",
    specific_exceptions=(AttributeError, RuntimeError),
    specific_message="Error in after_feature: {error}",
    fallback_message="Error in after_feature: {error}"
)
def after_feature(context: Any, feature: Any) -> None:
    """After each feature.

    Args:
        context: Behave context object
        feature: Behave feature object
    """
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

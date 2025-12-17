"""Behave hooks for Nemesis framework - Main coordinator."""
import traceback
from typing import Any, TYPE_CHECKING

from nemesis.infrastructure.logging import Logger

# Import hooks from specialized modules
from .feature_hooks import before_feature, after_feature
from .scenario_hooks import before_scenario, after_scenario
from .step_hooks import before_step, after_step

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
        LOGGER.info("Starting Nemesis test suite...")

        # Setup environment
        env_manager = _get_env_manager()
        success = env_manager.setup_environment(context)

        # Store env_manager in context for use by other hooks
        context.env_manager = env_manager

        if not success:
            LOGGER.warning("Environment setup failed, but continuing...")
        else:
            LOGGER.info("Environment setup completed successfully")

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError, ImportError) as e:
        # Environment setup errors
        LOGGER.error(f"Critical error in before_all: {e}", traceback=traceback.format_exc(), module=__name__, function="before_all")
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment setup
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.error(f"Critical error in before_all: {e}", traceback=traceback.format_exc(), module=__name__, function="before_all")
        raise


def after_all(context: Any) -> None:
    """Cleanup after all tests.

    Args:
        context: Behave context object
    """
    try:
        LOGGER.info("Ending Nemesis test suite...")

        # Determine final status
        status = "completed"
        if hasattr(context, 'test_failed') and context.test_failed:
            status = "failed"

        # Teardown environment
        env_manager = _get_env_manager()
        env_manager.teardown_environment(context, status)

        LOGGER.info(f"Test suite completed with status: {status}")

    except (KeyboardInterrupt, SystemExit):
        # Always re-raise these to allow proper program termination
        raise
    except (AttributeError, RuntimeError) as e:
        # Environment teardown errors - log but don't fail
        LOGGER.warning(f"Error in after_all: {e}", traceback=traceback.format_exc(), module=__name__, function="after_all")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave or environment teardown
        # NOTE: Behave framework may raise various exceptions we cannot predict
        LOGGER.warning(f"Error in after_all: {e}", traceback=traceback.format_exc(), module=__name__, function="after_all")


# Re-export hooks from specialized modules for Behave to discover
__all__ = [
    "before_all",
    "after_all",
    "before_feature",
    "after_feature",
    "before_scenario",
    "after_scenario",
    "before_step",
    "after_step",
]

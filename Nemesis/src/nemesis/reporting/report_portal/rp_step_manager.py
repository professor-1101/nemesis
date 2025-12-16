"""ReportPortal step management module.

This module manages ReportPortal step lifecycle within tests, handling starting
and finishing steps (BDD steps) within test scenarios, and maintaining step
hierarchy for detailed test execution tracking.
"""
from reportportal_client import RPClient
from nemesis.utils.decorators import retry, safe_execute
from nemesis.core.logging import Logger
from .rp_client_base import RPClientBase
from .rp_launch_manager import RPLaunchManager
from .rp_test_manager import RPTestManager
from .rp_utils import RPUtils

class RPStepManager:
    """Manages ReportPortal step lifecycle within tests.
    
    Handles starting and finishing steps (BDD steps) within test scenarios,
    maintaining step hierarchy for detailed test execution tracking.
    """
    def __init__(self, rp_client_base: RPClientBase, rp_launch_manager: RPLaunchManager, rp_test_manager: RPTestManager) -> None:
        """Initialize ReportPortal step manager.
        
        Args:
            rp_client_base: Base ReportPortal client
            rp_launch_manager: Launch manager instance
            rp_test_manager: Test manager instance
        """
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.rp_launch_manager = rp_launch_manager
        self.rp_test_manager = rp_test_manager
        self.logger = Logger.get_instance({})
        self.step_id: str | None = None

    @retry(max_attempts=2, delay=0.5)
    def start_step(self, step_name: str) -> None:
        """Start step with BDD formatting."""
        launch_id = self.rp_launch_manager.get_launch_id()
        test_id = self.rp_test_manager.get_test_id()

        if not test_id or not launch_id:
            self.logger.warning("Cannot start step: no active test or launch")
            return

        try:
            self.step_id = self.client.start_test_item(
                name=step_name,
                start_time=RPUtils.timestamp(),
                item_type="STEP",
                parent_item_id=test_id,
                launch_uuid=launch_id,
                has_stats=False,
            )

        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - start_test_item failed
            self.logger.error(f"Failed to start step - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK start_test_item may raise various exceptions we cannot predict
            self.logger.error(f"Failed to start step: {e}", exc_info=True)

    @safe_execute(log_exceptions=True)
    def finish_step(self, status: str) -> None:
        """Finish step."""
        if not self.step_id or not self.rp_launch_manager.is_launch_active():
            return

        try:
            self.client.finish_test_item(
                item_id=self.step_id,
                end_time=RPUtils.timestamp(),
                status=status,
                launch_uuid=self.rp_launch_manager.get_launch_id(),
            )
            self.step_id = None

        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - finish_test_item failed
            self.logger.error(f"Failed to finish step - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK finish_test_item may raise various exceptions we cannot predict
            self.logger.error(f"Failed to finish step: {e}", exc_info=True)

    def get_step_id(self) -> str | None:
        """Get the current step ID.
        
        Returns:
            Step ID if available, None otherwise
        """
        return self.step_id

"""ReportPortal step management module.

This module manages ReportPortal step lifecycle within tests, handling starting
and finishing steps (BDD steps) within test scenarios, and maintaining step
hierarchy for detailed test execution tracking.
"""
from reportportal_client import RPClient
from nemesis.utils.decorators import retry, safe_execute
from nemesis.infrastructure.logging import Logger
from .rp_client_base import RPClientBase
from .rp_launch_coordinator import RPLaunchCoordinator
from .rp_test_handler import RPTestHandler
from .rp_utils import RPUtils

class RPStepHandler:
    """Handles ReportPortal step lifecycle within tests.

    Handles starting and finishing steps (BDD steps) within test scenarios,
    maintaining step hierarchy for detailed test execution tracking.

    Supports three logging layouts:
    - SCENARIO: Steps logged as messages only (no test items)
    - STEP: Steps as flat test items under scenario
    - NESTED: Steps as nested test items (hierarchical)
    """
    def __init__(
        self,
        rp_client_base: RPClientBase,
        rp_launch_manager: RPLaunchCoordinator,
        rp_test_manager: RPTestHandler,
        step_log_layout: str = "NESTED"
    ) -> None:
        """Initialize ReportPortal step manager.

        Args:
            rp_client_base: Base ReportPortal client
            rp_launch_manager: Launch manager instance
            rp_test_manager: Test manager instance
            step_log_layout: Layout mode (SCENARIO, STEP, NESTED)
        """
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.rp_launch_manager = rp_launch_manager
        self.rp_test_manager = rp_test_manager
        self.logger = Logger.get_instance({})
        self.step_id: str | None = None
        self.step_log_layout = step_log_layout.upper()

        self.logger.info(f"RPStepHandler initialized with layout: {self.step_log_layout}")

    def should_create_step_item(self) -> bool:
        """Check if step should be created as test item based on layout.

        Returns:
            True if step item should be created, False if only logged
        """
        return self.step_log_layout in ("STEP", "NESTED")

    def log_step_as_message(self, step_name: str, status: str = "INFO") -> None:
        """Log step as message (for SCENARIO layout mode).

        Args:
            step_name: Name of the step
            status: Log level (INFO, WARN, ERROR)
        """
        test_id = self.rp_test_manager.get_test_id()
        if not test_id:
            return

        try:
            self.client.log(
                time=RPUtils.timestamp(),
                message=f"Step: {step_name}",
                level=status,
                item_id=test_id
            )
        except (AttributeError, RuntimeError) as e:
            self.logger.debug(f"Failed to log step as message: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.debug(f"Failed to log step as message: {e}", exc_info=True)

    @retry(max_attempts=2, delay=0.5)
    def start_step(self, step_name: str) -> None:
        """Start step with BDD formatting (respects layout mode).

        In SCENARIO mode: Logs step as message only
        In STEP/NESTED mode: Creates step as test item
        """
        # SCENARIO mode: Log as message only, don't create test item
        if self.step_log_layout == "SCENARIO":
            self.log_step_as_message(step_name, "INFO")
            return

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
        """Finish step (respects layout mode).

        In SCENARIO mode: No-op (step was logged as message)
        In STEP/NESTED mode: Finishes step test item
        """
        # SCENARIO mode: Nothing to finish (step was logged as message)
        if self.step_log_layout == "SCENARIO":
            return

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

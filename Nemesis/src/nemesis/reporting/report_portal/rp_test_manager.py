"""ReportPortal test (scenario) management module.

This module manages ReportPortal test scenario lifecycle, handling starting
and finishing test scenarios within features, and maintaining test hierarchy
for BDD-style test organization.
"""
from reportportal_client import RPClient
from nemesis.utils.decorators import retry, safe_execute
from nemesis.shared.exceptions import ReportPortalError
from nemesis.infrastructure.logging import Logger
from .rp_client_base import RPClientBase
from .rp_launch_manager import RPLaunchManager
from .rp_feature_manager import RPFeatureManager
from .rp_utils import RPUtils

class RPTestManager:
    """Manages ReportPortal test (scenario) lifecycle.
    
    Handles starting and finishing test scenarios within features,
    maintaining test hierarchy for BDD-style test organization.
    """
    def __init__(self, rp_client_base: RPClientBase, rp_launch_manager: RPLaunchManager, rp_feature_manager: RPFeatureManager) -> None:
        """Initialize ReportPortal test manager.
        
        Args:
            rp_client_base: Base ReportPortal client
            rp_launch_manager: Launch manager instance
            rp_feature_manager: Feature manager instance
        """
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.rp_launch_manager = rp_launch_manager
        self.rp_feature_manager = rp_feature_manager
        self.logger = Logger.get_instance({})
        self.test_id: str | None = None

    @retry(max_attempts=2, delay=0.5)
    def start_test(self, name: str, test_type: str = "SCENARIO") -> None:
        """Start test (scenario) under feature."""
        launch_id = self.rp_launch_manager.get_launch_id()
        feature_id = self.rp_feature_manager.get_feature_id()

        if not launch_id:
            self.logger.warning("Cannot start test: no active launch")
            return

        try:
            formatted_name = f"Scenario: {name}" if not name.startswith("Scenario:") else name

            # Clear previous test_id before starting new test
            self.test_id = None

            self.test_id = self.client.start_test_item(
                name=formatted_name,
                start_time=RPUtils.timestamp(),
                item_type=test_type,
                parent_item_id=feature_id,
                launch_uuid=launch_id,
            )

            if not self.test_id:
                raise ReportPortalError(
                    "Test ID is None",
                    f"ReportPortal did not return test ID for {name}"
                )

            self.logger.info(f"Scenario started: {name}")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - start_test_item failed
            raise ReportPortalError(f"Failed to start test: {name}", str(e)) from e
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK start_test_item may raise various exceptions we cannot predict
            raise ReportPortalError(f"Failed to start test: {name}", str(e)) from e

    @safe_execute(log_exceptions=True)
    def finish_test(self, status: str) -> None:
        """Finish test.

        Note: test_id is kept after finishing to allow attachments.
        It will be cleared when a new test starts or launch finishes.
        """
        if not self.test_id or not self.rp_launch_manager.is_launch_active():
            return

        try:
            self.client.finish_test_item(
                item_id=self.test_id,
                end_time=RPUtils.timestamp(),
                status=status,
                launch_uuid=self.rp_launch_manager.get_launch_id(),
            )
            # Keep test_id for potential attachments after test finish
            # It will be cleared when a new test starts or launch finishes
            # self.test_id = None

        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - finish_test_item failed
            self.logger.error(f"Failed to finish test - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK finish_test_item may raise various exceptions we cannot predict
            self.logger.error(f"Failed to finish test: {e}", exc_info=True)

    def get_test_id(self) -> str | None:
        """Get the current test (scenario) ID.
        
        Returns:
            Test ID if available, None otherwise
        """
        return self.test_id

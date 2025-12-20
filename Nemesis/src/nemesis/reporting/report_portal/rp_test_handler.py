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
from .rp_launch_coordinator import RPLaunchCoordinator
from .rp_feature_handler import RPFeatureHandler
from .rp_utils import RPUtils

class RPTestHandler:
    """Handles ReportPortal test (scenario) lifecycle.
    
    Handles starting and finishing test scenarios within features,
    maintaining test hierarchy for BDD-style test organization.
    """
    def __init__(self, rp_client_base: RPClientBase, rp_launch_manager: RPLaunchCoordinator, rp_feature_manager: RPFeatureHandler, is_skipped_an_issue: bool = False) -> None:
        """Initialize ReportPortal test manager.

        Args:
            rp_client_base: Base ReportPortal client
            rp_launch_manager: Launch manager instance
            rp_feature_manager: Feature manager instance
            is_skipped_an_issue: Whether skipped tests should be marked as issues
        """
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.rp_launch_manager = rp_launch_manager
        self.rp_feature_manager = rp_feature_manager
        self.logger = Logger.get_instance({})
        self.test_id: str | None = None
        self.is_skipped_an_issue = is_skipped_an_issue

    @retry(max_attempts=2, delay=0.5)
    def start_test(self, name: str, test_type: str = "TEST", tags: list = None, description: str = "") -> None:
        """Start test (scenario) under feature with support for advanced tags.

        Args:
            name: Scenario name
            test_type: Test item type (default: SCENARIO)
            tags: List of Behave tags (supports @attribute, @test_case_id, etc.)
            description: Scenario description
        """
        launch_id = self.rp_launch_manager.get_launch_id()
        feature_id = self.rp_feature_manager.get_feature_id()

        if not launch_id:
            self.logger.warning("Cannot start test: no active launch")
            return

        try:
            # Use scenario name directly (without "Scenario:" prefix)
            # ReportPortal will show it as a scenario item based on item_type
            formatted_name = name

            # Clear previous test_id before starting new test
            # This ensures each scenario gets its own test_id
            if self.test_id:
                self.logger.debug(f"Clearing previous test_id: {self.test_id} before starting new test: {name}")
            self.test_id = None

            # Parse tags for attributes and metadata
            parsed_tags = RPUtils.parse_behave_tags(tags or [])
            attributes = parsed_tags.get('attributes', [])
            test_case_id = parsed_tags.get('test_case_id')

            # Build start_test_item parameters
            start_params = {
                "name": formatted_name,
                "start_time": RPUtils.timestamp(),
                "item_type": test_type,
                "parent_item_id": feature_id,
                "launch_uuid": launch_id,
            }

            # Add description if present
            if description:
                start_params["description"] = description

            # Add attributes if present
            if attributes:
                start_params["attributes"] = attributes
                self.logger.debug(f"Scenario attributes: {attributes}")

            # Add test_case_id if present
            if test_case_id:
                start_params["test_case_id"] = test_case_id
                self.logger.debug(f"Scenario test_case_id: {test_case_id}")

            self.test_id = self.client.start_test_item(**start_params)

            if not self.test_id:
                raise ReportPortalError(
                    "Test ID is None",
                    f"ReportPortal did not return test ID for {name}"
                )

            self.logger.info(f"Scenario started: {name} (attributes: {len(attributes)}, test_case_id: {test_case_id})")

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
        """Finish test with optional issue marking for skipped tests.

        Note: test_id is kept after finishing to allow attachments.
        It will be cleared when a new test starts or launch finishes.

        Args:
            status: Test status (PASSED, FAILED, SKIPPED, etc.)
        """
        if not self.test_id:
            self.logger.warning(f"[RP DEBUG] finish_test: test_id is None, skipping finish")
            return
        
        if not self.rp_launch_manager.is_launch_active():
            self.logger.warning(f"[RP DEBUG] finish_test: launch is not active (launch_id={self.rp_launch_manager.launch_id}), skipping finish")
            return
        
        self.logger.info(f"[RP DEBUG] finish_test: test_id={self.test_id}, status={status}, launch_id={self.rp_launch_manager.get_launch_id()}")

        try:
            finish_params = {
                "item_id": self.test_id,
                "end_time": RPUtils.timestamp(),
                "status": status,
                "launch_uuid": self.rp_launch_manager.get_launch_id(),
            }

            # Handle skipped tests based on is_skipped_an_issue configuration
            if status == "SKIPPED" and not self.is_skipped_an_issue:
                # Mark skipped tests as NOT an issue
                finish_params["issue"] = {
                    "issue_type": "NOT_ISSUE"
                }

            self.logger.info(f"[RP DEBUG] Calling client.finish_test_item with params: item_id={finish_params['item_id']}, status={finish_params['status']}, launch_uuid={finish_params['launch_uuid']}")
            self.client.finish_test_item(**finish_params)
            self.logger.info(f"[RP DEBUG] finish_test_item completed successfully for test_id={self.test_id}")
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

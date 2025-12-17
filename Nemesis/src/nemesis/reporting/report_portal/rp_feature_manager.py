"""ReportPortal feature (test suite) management module.

This module manages ReportPortal feature lifecycle, handling starting and finishing
features within a launch, and maintaining feature hierarchy for test organization.
"""
from reportportal_client import RPClient
from nemesis.utils.decorators import retry, safe_execute
from nemesis.infrastructure.logging import Logger
from .rp_client_base import RPClientBase
from .rp_launch_manager import RPLaunchManager
from .rp_utils import RPUtils

class RPFeatureManager:
    """Manages ReportPortal feature (test suite) lifecycle.
    
    Handles starting and finishing features within a launch, maintaining
    feature hierarchy for test organization.
    """
    def __init__(self, rp_client_base: RPClientBase, rp_launch_manager: RPLaunchManager) -> None:
        """Initialize ReportPortal feature manager.
        
        Args:
            rp_client_base: Base ReportPortal client
            rp_launch_manager: Launch manager instance
        """
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.rp_launch_manager = rp_launch_manager
        self.logger = Logger.get_instance({})
        self.feature_id: str | None = None

    @retry(max_attempts=2, delay=0.5)
    def start_feature(self, feature_name: str, description: str = "") -> None:
        """Start feature as SUITE."""
        launch_id = self.rp_launch_manager.get_launch_id()
        if not launch_id:
            self.logger.warning("Cannot start feature: no active launch")
            return

        try:
            self.feature_id = self.client.start_test_item(
                name=f"Feature: {feature_name}",
                start_time=RPUtils.timestamp(),
                item_type="SUITE",
                description=description,
                launch_uuid=launch_id,
            )
            self.logger.info(f"Feature started: {feature_name}")
        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - start_test_item failed
            self.logger.error(f"Failed to start feature - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK start_test_item may raise various exceptions we cannot predict
            self.logger.error(f"Failed to start feature: {e}", exc_info=True)

    @safe_execute(log_exceptions=True)
    def finish_feature(self, status: str = "PASSED") -> None:
        """Finish feature."""
        if not self.feature_id or not self.rp_launch_manager.is_launch_active():
            return

        try:
            self.client.finish_test_item(
                item_id=self.feature_id,
                end_time=RPUtils.timestamp(),
                status=status,
                launch_uuid=self.rp_launch_manager.get_launch_id(),
            )
            self.feature_id = None
        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors - finish_test_item failed
            self.logger.error(f"Failed to finish feature - API error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK finish_test_item may raise various exceptions we cannot predict
            self.logger.error(f"Failed to finish feature: {e}", exc_info=True)

    def get_feature_id(self) -> str | None:
        """Get the current feature ID.
        
        Returns:
            Feature ID if available, None otherwise
        """
        return self.feature_id

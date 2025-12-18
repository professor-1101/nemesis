"""Base class for ReportPortal handlers with common initialization."""

from reportportal_client import RPClient
from nemesis.infrastructure.logging import Logger
from .rp_client_base import RPClientBase
from .rp_launch_manager import RPLaunchManager
from .rp_feature_manager import RPFeatureManager
from .rp_test_manager import RPTestManager
from .rp_step_manager import RPStepManager


class RPBaseHandler:
    """Base class for ReportPortal handlers with shared initialization.

    Provides common initialization pattern for handlers that need access to
    RP client and all manager instances.
    """

    def __init__(
        self,
        rp_client_base: RPClientBase,
        rp_launch_manager: RPLaunchManager,
        rp_feature_manager: RPFeatureManager,
        rp_test_manager: RPTestManager,
        rp_step_manager: RPStepManager
    ) -> None:
        """Initialize base manager with shared dependencies.

        Args:
            rp_client_base: Base ReportPortal client
            rp_launch_manager: Launch manager instance
            rp_feature_manager: Feature manager instance
            rp_test_manager: Test manager instance
            rp_step_manager: Step manager instance
        """
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.rp_launch_manager = rp_launch_manager
        self.rp_feature_manager = rp_feature_manager
        self.rp_test_manager = rp_test_manager
        self.rp_step_manager = rp_step_manager
        self.logger = Logger.get_instance({})

    def _get_current_item_id(self) -> str | None:
        """Get current item ID (step > test > feature).

        Returns:
            Current item ID or None if no active item
        """
        return (
            self.rp_step_manager.get_step_id()
            or self.rp_test_manager.get_test_id()
            or self.rp_feature_manager.get_feature_id()
        )

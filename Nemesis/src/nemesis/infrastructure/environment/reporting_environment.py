"""Reporting environment management for Nemesis framework."""
from typing import Any, Optional

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.reporting.coordinator import ReportCoordinator
from nemesis.reporting.attachments import AttachmentHandler
from nemesis.infrastructure.environment.scenario_attachment_handler import ScenarioAttachmentHandler
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class ReportingEnvironment:
    """Manages reporting setup and lifecycle."""

    def __init__(self, config: ConfigLoader) -> None:
        """Initialize reporting environment.

        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.logger = Logger.get_instance({})
        self.report_manager: Optional[ReportCoordinator] = None
        self.attachment_handler: Optional[AttachmentHandler] = None
        self.attachment_handler_instance: Optional[ScenarioAttachmentHandler] = None

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError, ImportError),
        specific_message="Reporting environment setup failed: {error}",
        fallback_message="Reporting environment setup failed: {error}",
        return_on_error=False
    )
    def setup(self, context: Any) -> bool:
        """Setup reporting environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        self.logger.info("Setting up reporting environment...")

        # Check if reporting is enabled
        if not self.config.get("reporting.local.enabled", True):
            self.logger.info("Local reporting disabled, skipping setup")
            return True

        # Initialize report manager
        self.report_manager = ReportCoordinator(context)
        context.report_manager = self.report_manager

        # Initialize attachment handler
        self.attachment_handler = AttachmentHandler(context.execution_id)
        context.attachment_handler = self.attachment_handler

        # Initialize scenario attachment handler (will be created when report_manager is ready)
        self.attachment_handler_instance = None

        self.logger.info("Reporting environment setup completed")
        return True

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error during reporting teardown: {error}",
        fallback_message="Error during reporting teardown: {error}"
    )
    def teardown(self, _context: Any, _status: str) -> None:
        """Teardown reporting environment.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            _status: Test execution status (unused, kept for interface compatibility)
        """
        self.logger.info("Tearing down reporting environment...")

        # Finalize reports
        if self.report_manager:
            # Note: ReportCoordinator has finalize() method, not finalize_reports()
            # Finalization happens in CLI _finalize_reports(), not here
            pass

        self.logger.info("Reporting environment teardown completed")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error starting test suite reporting: {error}",
        fallback_message="Error starting test suite reporting: {error}"
    )
    def start_test_suite(self, _context: Any) -> None:
        """Start test suite reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
        """
        if self.report_manager:
            self.report_manager.start_test_suite()
            self.logger.info("Test suite reporting started")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error ending test suite reporting: {error}",
        fallback_message="Error ending test suite reporting: {error}"
    )
    def end_test_suite(self, _context: Any, status: str) -> None:
        """End test suite reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            status: Test execution status
        """
        if self.report_manager:
            self.report_manager.end_test_suite(status)
            self.logger.info(f"Test suite reporting ended (status: {status})")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error starting feature reporting: {error}",
        fallback_message="Error starting feature reporting: {error}"
    )
    def start_feature(self, _context: Any, feature: Any) -> None:
        """Start feature reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            feature: Behave feature object
        """
        feature_name = getattr(feature, 'name', str(feature))
        self.logger.info(f"[RP DEBUG] ReportingEnvironment.start_feature called: feature_name={feature_name}")
        
        if self.report_manager:
            self.logger.info(f"[RP DEBUG] Calling report_manager.start_feature for: {feature_name}")
            self.report_manager.start_feature(feature)
            self.logger.info(f"[RP DEBUG] Feature reporting started: {feature_name}")
        else:
            self.logger.warning(f"[RP DEBUG] report_manager is None, cannot start feature: {feature_name}")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error ending feature reporting: {error}",
        fallback_message="Error ending feature reporting: {error}"
    )
    def end_feature(self, _context: Any, feature: Any, status: str) -> None:
        """End feature reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            feature: Behave feature object
            status: Feature execution status ("passed" or "failed")
        """
        if self.report_manager:
            self.report_manager.end_feature(feature, status)
            self.logger.debug(f"Feature reporting ended: {feature.name} (status: {status})")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error starting scenario reporting: {error}",
        fallback_message="Error starting scenario reporting: {error}"
    )
    def start_scenario(self, _context: Any, scenario: Any) -> None:
        """Start scenario reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            scenario: Behave scenario object
        """
        if self.report_manager:
            self.report_manager.start_scenario(scenario)
            self.logger.debug(f"Scenario reporting started: {scenario.name}")
        else:
            self.logger.warning("Report manager not available for scenario reporting")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, AttributeError, RuntimeError),
        specific_message="Failed to attach scenario videos - {error}",
        fallback_message="Failed to attach scenario videos: {error}"
    )
    def _attach_scenario_videos(self, context: Any, scenario: Any) -> None:
        """Attach scenario videos to report.

        Args:
            context: Behave context object
            scenario: Behave scenario object
        """
        if self.attachment_handler_instance:
            self.attachment_handler_instance.attach_videos(context, scenario)

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, AttributeError, RuntimeError),
        specific_message="Failed to attach scenario collectors - {error}",
        fallback_message="Failed to attach scenario collectors: {error}"
    )
    def _attach_scenario_collectors(self, context: Any, scenario: Any) -> None:
        """Attach scenario collectors to report.

        Args:
            context: Behave context object
            scenario: Behave scenario object
        """
        if self.attachment_handler_instance:
            self.attachment_handler_instance.attach_collectors(context, scenario)

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error ending scenario reporting: {error}",
        fallback_message="Error ending scenario reporting: {error}"
    )
    def end_scenario(self, context: Any, scenario: Any, status: str) -> None:
        """End scenario reporting.

        Args:
            context: Behave context object
            scenario: Behave scenario object
            status: Scenario execution status
        """
        if self.report_manager:
            # IMPORTANT: Attach attachments BEFORE finishing the test in ReportPortal
            # This ensures test_id is still available for attachment
            # Note: Attachments are attached to the active test/scenario, so must happen before finish_test

            # Initialize attachment handler if not already done
            if not self.attachment_handler_instance:
                self.attachment_handler_instance = ScenarioAttachmentHandler(self.report_manager)

            # Attach videos and collectors (exception handling via decorators on helper methods)
            self._attach_scenario_videos(context, scenario)
            self._attach_scenario_collectors(context, scenario)

            self.report_manager.end_scenario(scenario, status)
            self.logger.debug(f"Scenario reporting ended: {scenario.name} (status: {status})")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error starting step reporting: {error}",
        fallback_message="Error starting step reporting: {error}"
    )
    def start_step(self, _context: Any, step: Any) -> None:
        """Start step reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            step: Behave step object
        """
        if self.report_manager:
            self.report_manager.start_step(step)

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error ending step reporting: {error}",
        fallback_message="Error ending step reporting: {error}"
    )
    def end_step(self, _context: Any, step: Any, status: str) -> None:
        """End step reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            step: Behave step object
            status: Step execution status
        """
        if self.report_manager:
            self.report_manager.end_step(step, status)

    def get_report_manager(self) -> Optional[ReportCoordinator]:
        """Get report manager instance."""
        return self.report_manager

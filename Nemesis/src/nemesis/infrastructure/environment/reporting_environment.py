"""Reporting environment management for Nemesis framework."""
import traceback
from typing import Any, Optional

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.reporting.coordinator import ReportCoordinator
from nemesis.reporting.attachments import AttachmentHandler
from nemesis.infrastructure.environment.scenario_attachment_handler import ScenarioAttachmentHandler


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

    def setup(self, context: Any) -> bool:
        """Setup reporting environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        try:
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

        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except (AttributeError, RuntimeError, ImportError) as e:
            # ReportCoordinator or AttachmentHandler initialization errors
            self.logger.warning(f"Reporting environment setup failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="setup")
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator initialization
            # NOTE: ReportCoordinator or AttachmentHandler may raise various exceptions we cannot predict
            self.logger.warning(f"Reporting environment setup failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="setup")
            return False

    def teardown(self, _context: Any, _status: str) -> None:
        """Teardown reporting environment.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            _status: Test execution status (unused, kept for interface compatibility)
        """
        try:
            self.logger.info("Tearing down reporting environment...")

            # Finalize reports
            if self.report_manager:
                # Note: ReportCoordinator has finalize() method, not finalize_reports()
                # Finalization happens in CLI _finalize_reports(), not here
                pass

            self.logger.info("Reporting environment teardown completed")

        except (AttributeError, RuntimeError) as e:
            # Reporting teardown errors
            self.logger.error(f"Error during reporting teardown: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="teardown")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from reporting teardown operations
            # NOTE: ReportCoordinator teardown may raise various exceptions we cannot predict
            self.logger.error(f"Error during reporting teardown: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="teardown")

    def start_test_suite(self, _context: Any) -> None:
        """Start test suite reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
        """
        try:
            if self.report_manager:
                self.report_manager.start_test_suite()
                self.logger.info("Test suite reporting started")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error starting test suite reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_test_suite")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.start_test_suite
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error starting test suite reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_test_suite")

    def end_test_suite(self, _context: Any, status: str) -> None:
        """End test suite reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            status: Test execution status
        """
        try:
            if self.report_manager:
                self.report_manager.end_test_suite(status)
                self.logger.info(f"Test suite reporting ended (status: {status})")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error ending test suite reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_test_suite")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.end_test_suite
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error ending test suite reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_test_suite")

    def start_feature(self, _context: Any, feature: Any) -> None:
        """Start feature reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            feature: Behave feature object
        """
        try:
            if self.report_manager:
                self.report_manager.start_feature(feature)
                self.logger.debug(f"Feature reporting started: {feature.name}")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error starting feature reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_feature")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.start_feature
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error starting feature reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_feature")

    def end_feature(self, _context: Any, feature: Any, status: str) -> None:
        """End feature reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            feature: Behave feature object
            status: Feature execution status ("passed" or "failed")
        """
        try:
            if self.report_manager:
                self.report_manager.end_feature(feature, status)
                self.logger.debug(f"Feature reporting ended: {feature.name} (status: {status})")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error ending feature reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_feature")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.end_feature
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error ending feature reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_feature")

    def start_scenario(self, _context: Any, scenario: Any) -> None:
        """Start scenario reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            scenario: Behave scenario object
        """
        try:
            if self.report_manager:
                self.report_manager.start_scenario(scenario)
                self.logger.debug(f"Scenario reporting started: {scenario.name}")
            else:
                self.logger.warning("Report manager not available for scenario reporting")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error starting scenario reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_scenario")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.start_scenario
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error starting scenario reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_scenario")

    def end_scenario(self, context: Any, scenario: Any, status: str) -> None:
        """End scenario reporting.

        Args:
            context: Behave context object
            scenario: Behave scenario object
            status: Scenario execution status
        """
        try:
            if self.report_manager:
                # IMPORTANT: Attach attachments BEFORE finishing the test in ReportPortal
                # This ensures test_id is still available for attachment
                # Note: Attachments are attached to the active test/scenario, so must happen before finish_test

                # Initialize attachment handler if not already done
                if not self.attachment_handler_instance:
                    self.attachment_handler_instance = ScenarioAttachmentHandler(self.report_manager)

                try:
                    self.attachment_handler_instance.attach_videos(context, scenario)
                except (OSError, IOError) as e:
                    # Video file I/O errors
                    self.logger.warning(f"Failed to attach scenario videos - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors
                    self.logger.warning(f"Failed to attach scenario videos - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from video attachment
                    # NOTE: Video attachment operations may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to attach scenario videos: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")

                try:
                    self.attachment_handler_instance.attach_collectors(context, scenario)
                except (OSError, IOError) as e:
                    # Collector file I/O errors
                    self.logger.warning(f"Failed to attach scenario collectors - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors
                    self.logger.warning(f"Failed to attach scenario collectors - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from collector attachment
                    # NOTE: Collector attachment operations may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to attach scenario collectors: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")

                self.report_manager.end_scenario(scenario, status)
                self.logger.debug(f"Scenario reporting ended: {scenario.name} (status: {status})")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error ending scenario reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.end_scenario
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error ending scenario reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_scenario")

    def start_step(self, _context: Any, step: Any) -> None:
        """Start step reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            step: Behave step object
        """
        try:
            if self.report_manager:
                self.report_manager.start_step(step)

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error starting step reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_step")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.start_step
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error starting step reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="start_step")

    def end_step(self, _context: Any, step: Any, status: str) -> None:
        """End step reporting.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            step: Behave step object
            status: Step execution status
        """
        try:
            if self.report_manager:
                self.report_manager.end_step(step, status)

        except (AttributeError, RuntimeError) as e:
            # ReportPortal or local reporter API errors
            self.logger.warning(f"Error ending step reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_step")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportCoordinator.end_step
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.warning(f"Error ending step reporting: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportingEnvironment", method="end_step")

    def get_report_manager(self) -> Optional[ReportCoordinator]:
        """Get report manager instance."""
        return self.report_manager

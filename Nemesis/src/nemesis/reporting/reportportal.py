"""ReportPortal integration """
import traceback
from pathlib import Path

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from .report_portal.rp_config_loader import RPConfigLoader
from .report_portal.rp_client_base import RPClientBase
from .report_portal.rp_launch_manager import RPLaunchManager
from .report_portal.rp_feature_manager import RPFeatureManager
from .report_portal.rp_test_manager import RPTestManager
from .report_portal.rp_step_manager import RPStepManager
from .report_portal.rp_logger import RPLogger
from .report_portal.rp_attachment_manager import RPAttachmentManager

class ReportPortalClient:
    """ReportPortal client with BDD-optimized formatting."""

    def __init__(self, config: ConfigLoader) -> None:
        self.config = config
        self.logger = Logger.get_instance({})

        # Check if ReportPortal is enabled before initializing
        if not config.get("reporting.reportportal.enabled", False):
            self.logger.info("ReportPortal is disabled, skipping initialization")
            self.rp_client_base = None
            self.rp_launch_manager = None
            self.rp_feature_manager = None
            self.rp_test_manager = None
            self.rp_step_manager = None
            self.rp_logger = None
            self.rp_attachment_manager = None
            return

        self.config_loader = RPConfigLoader(config)
        rp_settings = self.config_loader.get_rp_settings()

        self.rp_client_base = RPClientBase(
            endpoint=rp_settings["endpoint"],
            project=rp_settings["project"],
            api_key=rp_settings["api_key"],
            verify_ssl=rp_settings.get("verify_ssl", True),
        )
        self.rp_client_base._validate_connection() # Initial connection validation

        self.rp_launch_manager = RPLaunchManager(
            rp_client_base=self.rp_client_base,
            launch_name=rp_settings["launch_name"],
            launch_description=rp_settings["launch_description"],
            launch_attributes=rp_settings["launch_attributes"],
        )
        self.rp_feature_manager = RPFeatureManager(self.rp_client_base, self.rp_launch_manager)
        self.rp_test_manager = RPTestManager(self.rp_client_base, self.rp_launch_manager, self.rp_feature_manager)
        self.rp_step_manager = RPStepManager(self.rp_client_base, self.rp_launch_manager, self.rp_test_manager)
        self.rp_logger = RPLogger(self.rp_client_base, self.rp_launch_manager, self.rp_feature_manager, self.rp_test_manager, self.rp_step_manager)
        self.rp_attachment_manager = RPAttachmentManager(self.rp_client_base, self.rp_launch_manager, self.rp_feature_manager, self.rp_test_manager, self.rp_step_manager)

        # Only start launch if not already started (check RPClient internal state)
        # RPClient may already have a launch_id from a previous initialization
        existing_launch_id = getattr(self.rp_client_base.client, 'launch_id', None)

        # Also check if launch_id was stored in EnvironmentManager (for finalization phase)
        saved_launch_id = None
        if not existing_launch_id and not self.rp_launch_manager.launch_id:
            try:
                from nemesis.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                env_manager = _get_env_manager()
                if env_manager and hasattr(env_manager, 'rp_launch_id') and env_manager.rp_launch_id:
                    saved_launch_id = env_manager.rp_launch_id
                    self.logger.info(f"Found launch_id in EnvironmentManager: {saved_launch_id}")
            except (ImportError, AttributeError) as load_error:
                # Non-critical: failed to get launch_id from EnvironmentManager
                self.logger.debug(f"Failed to get launch_id from EnvironmentManager: {load_error}", module=__name__, class_name="ReportPortalClient", method="__init__")
            except (KeyboardInterrupt, SystemExit):
                # Allow program interruption to propagate
                raise
            except Exception as load_error:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from EnvironmentManager access
                # NOTE: EnvironmentManager import or access may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to get launch_id from EnvironmentManager: {load_error}", module=__name__, class_name="ReportPortalClient", method="__init__")

        if not existing_launch_id and not self.rp_launch_manager.launch_id and not saved_launch_id:
            self.rp_launch_manager.start_launch()
        elif existing_launch_id:
            # Reuse existing launch_id from RPClient
            self.rp_launch_manager.launch_id = existing_launch_id
            self.logger.info(f"Reusing existing ReportPortal launch: {existing_launch_id}")
        elif saved_launch_id:
            # Reuse saved launch_id from EnvironmentManager (from previous process or same process)
            self.rp_launch_manager.launch_id = saved_launch_id
            # Note: Cannot set client.launch_id directly (it's read-only property)
            # But RPClient will use the launch_id from finish_launch call
            self.logger.info(f"Reusing launch_id from EnvironmentManager: {saved_launch_id}")

    def start_launch(self) -> None:
        """Start launch - only if not already started."""
        if self.rp_launch_manager:
            self.rp_launch_manager.start_launch()

    def start_feature(self, feature_name: str, description: str = "") -> None:
        """Start a feature (test suite) in ReportPortal.
        
        Args:
            feature_name: Name of the feature to start
            description: Optional description for the feature
        """
        if self.rp_feature_manager:
            self.rp_feature_manager.start_feature(feature_name, description)

    def finish_feature(self, status: str = "PASSED") -> None:
        """Finish a feature (test suite) in ReportPortal.
        
        Args:
            status: Final status of the feature (PASSED, FAILED, etc.)
        """
        if self.rp_feature_manager:
            self.rp_feature_manager.finish_feature(status)

    def start_test(self, name: str, test_type: str = "SCENARIO") -> None:
        """Start a test (scenario) in ReportPortal.
        
        Args:
            name: Name of the test/scenario to start
            test_type: Type of test item (SCENARIO, TEST, etc.)
        """
        if self.rp_test_manager:
            self.rp_test_manager.start_test(name, test_type)

    def start_step(self, step_name: str) -> None:
        """Start a step within a test in ReportPortal.
        
        Args:
            step_name: Name of the step to start
        """
        if self.rp_step_manager:
            self.rp_step_manager.start_step(step_name)

    def finish_step(self, status: str) -> None:
        """Finish a step in ReportPortal.
        
        Args:
            status: Final status of the step (PASSED, FAILED, etc.)
        """
        if self.rp_step_manager:
            self.rp_step_manager.finish_step(status)

    def finish_test(self, status: str) -> None:
        """Finish a test (scenario) in ReportPortal.
        
        Args:
            status: Final status of the test (PASSED, FAILED, etc.)
        """
        if self.rp_test_manager:
            self.rp_test_manager.finish_test(status)

    def finish_launch(self, status: str = "FINISHED", launch_id: str | None = None) -> None:
        """Finish a launch in ReportPortal.
        
        Args:
            status: Final status of the launch (FINISHED, FAILED, etc.)
            launch_id: Optional launch ID to finish (uses current launch if not provided)
        """
        if self.rp_launch_manager:
            # If launch_id provided, use it; otherwise use the one from launch_manager
            target_launch_id = launch_id or self.launch_id
            self.rp_launch_manager.finish_launch(status, target_launch_id)

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log a message to ReportPortal.
        
        Args:
            message: Message text to log
            level: Log level (INFO, DEBUG, WARN, ERROR, etc.)
        """
        if self.rp_logger:
            self.rp_logger.log_message(message, level)

    def log_exception(self, exception: Exception, description: str = "") -> None:
        """Log an exception to ReportPortal with full stack trace.
        
        Args:
            exception: Exception object to log
            description: Optional description/context for the exception
        """
        if self.rp_logger:
            self.rp_logger.log_exception(exception, description)

    def log_exception_with_attachment(self, exception: Exception, attachment_path: Path = None, description: str = "") -> None:
        """Log an exception to ReportPortal with an attachment file.
        
        Args:
            exception: Exception object to log
            attachment_path: Optional path to file to attach with the exception
            description: Optional description/context for the exception
        """
        if self.rp_logger:
            self.rp_logger.log_exception_with_attachment(exception, attachment_path, description)
            if attachment_path and attachment_path.exists() and self.rp_attachment_manager:
                self.rp_attachment_manager.attach_file(attachment_path, f"Attachment for {type(exception).__name__}", "exception")

    def attach_file(self, file_path: Path, description: str = "", attachment_type: str = "") -> None:
        """Attach a file to the current test item in ReportPortal.
        
        Args:
            file_path: Path to the file to attach
            description: Optional description for the attachment
            attachment_type: Optional type of attachment (screenshot, video, etc.)
        """
        if self.rp_attachment_manager:
            self.rp_attachment_manager.attach_file(file_path, description, attachment_type)

    def is_healthy(self) -> bool:
        """Check if ReportPortal client is healthy and has an active launch.
        
        Returns:
            True if launch is active, False otherwise
        """
        if self.rp_launch_manager:
            return self.rp_launch_manager.is_launch_active()
        return False

    def get_launch_url(self) -> str | None:
        """Get the URL to the current launch in ReportPortal.
        
        Returns:
            Launch URL if available, None otherwise
        """
        if self.rp_launch_manager:
            return self.rp_launch_manager.get_launch_url()
        return None

    @property
    def launch_id(self) -> str | None:
        """Get the current launch ID."""
        if self.rp_launch_manager:
            return self.rp_launch_manager.launch_id
        return None

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        """Cleanup on context exit."""
        try:
            if self.rp_launch_manager and self.rp_launch_manager.is_launch_active():
                self.rp_launch_manager.finish_launch("FINISHED" if not exc_type else "FAILED")
            if hasattr(self, 'rp_client_base') and self.rp_client_base and hasattr(self.rp_client_base, 'client') and self.rp_client_base.client:
                try:
                    self.rp_client_base.client.terminate()
                except (AttributeError, RuntimeError) as terminate_error:
                    # RP client termination errors
                    self.logger.debug(f"Error terminating RP client: {terminate_error}", traceback=traceback.format_exc(), module=__name__, class_name="ReportPortalClient", method="__exit__")
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as terminate_error:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from RP client termination
                    # NOTE: ReportPortal SDK terminate() may raise various exceptions we cannot predict
                    self.logger.debug(f"Error terminating RP client: {terminate_error}", traceback=traceback.format_exc(), module=__name__, class_name="ReportPortalClient", method="__exit__")
        except (AttributeError, RuntimeError) as e:
            # ReportPortal cleanup errors
            self.logger.error(f"Error during ReportPortal cleanup: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportPortalClient", method="__exit__")
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal cleanup
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.error(f"Error during ReportPortal cleanup: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportPortalClient", method="__exit__")
        return False

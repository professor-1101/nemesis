"""ReportPortal integration """
import traceback
from pathlib import Path

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from .report_portal.rp_config_loader import RPConfigLoader
from .report_portal.rp_client_base import RPClientBase
from .report_portal.rp_launch_coordinator import RPLaunchCoordinator
from .report_portal.rp_feature_handler import RPFeatureHandler
from .report_portal.rp_test_handler import RPTestHandler
from .report_portal.rp_step_handler import RPStepHandler
from .report_portal.rp_logger import RPLogger
from .report_portal.rp_attachment_handler import RPAttachmentHandler

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

        # Store settings for lazy launch start (will be started in first feature if needed)
        self._launch_settings = rp_settings
        self._launch_started = False
        self._finished_launch_id = None  # Store launch_id after finish for finalization
        
        self.rp_launch_manager = RPLaunchCoordinator(
            rp_client_base=self.rp_client_base,
            launch_name=rp_settings["launch_name"],
            launch_description=rp_settings["launch_description"],
            launch_attributes=rp_settings["launch_attributes"],
            debug_mode=rp_settings.get("debug_mode", False),
        )
        self.rp_feature_manager = RPFeatureHandler(self.rp_client_base, self.rp_launch_manager)
        self.rp_test_manager = RPTestHandler(
            self.rp_client_base,
            self.rp_launch_manager,
            self.rp_feature_manager,
            is_skipped_an_issue=rp_settings.get("is_skipped_an_issue", False)
        )
        self.rp_step_manager = RPStepHandler(
            self.rp_client_base,
            self.rp_launch_manager,
            self.rp_test_manager,
            rp_settings.get("step_log_layout", "NESTED")
        )
        self.rp_logger = RPLogger(self.rp_client_base, self.rp_launch_manager, self.rp_feature_manager, self.rp_test_manager, self.rp_step_manager)
        self.rp_attachment_manager = RPAttachmentHandler(self.rp_client_base, self.rp_launch_manager, self.rp_feature_manager, self.rp_test_manager, self.rp_step_manager)

        # Only start launch if not already started (check RPClient internal state)
        # RPClient may already have a launch_id from a previous initialization
        existing_launch_id = getattr(self.rp_client_base.client, 'launch_id', None)

        # Also check if launch_id was stored in EnvironmentCoordinator (for finalization phase)
        saved_launch_id = None
        if not existing_launch_id and not self.rp_launch_manager.launch_id:
            try:
                from nemesis.infrastructure.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                env_manager = _get_env_manager()
                if env_manager and hasattr(env_manager, 'rp_launch_id') and env_manager.rp_launch_id:
                    saved_launch_id = env_manager.rp_launch_id
                    self.logger.info(f"Found launch_id in EnvironmentCoordinator: {saved_launch_id}")
            except (ImportError, AttributeError) as load_error:
                # Non-critical: failed to get launch_id from EnvironmentCoordinator
                self.logger.debug(f"Failed to get launch_id from EnvironmentCoordinator: {load_error}", module=__name__, class_name="ReportPortalClient", method="__init__")
            except (KeyboardInterrupt, SystemExit):
                # Allow program interruption to propagate
                raise
            except Exception as load_error:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from EnvironmentCoordinator access
                # NOTE: EnvironmentCoordinator import or access may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to get launch_id from EnvironmentCoordinator: {load_error}", module=__name__, class_name="ReportPortalClient", method="__init__")

        if existing_launch_id:
            # Reuse existing launch_id from RPClient
            self.rp_launch_manager.launch_id = existing_launch_id
            self._launch_started = True
            self.logger.info(f"Reusing existing ReportPortal launch: {existing_launch_id}")
        elif saved_launch_id:
            # Reuse saved launch_id from EnvironmentCoordinator (from previous process or same process)
            self.rp_launch_manager.launch_id = saved_launch_id
            self._launch_started = True
            # Note: Cannot set client.launch_id directly (it's read-only property)
            # But RPClient will use the launch_id from finish_launch call
            self.logger.info(f"Reusing launch_id from EnvironmentCoordinator: {saved_launch_id}")
        # Don't start launch here - will be started lazily in first feature if needed

    def start_launch(self, launch_description: str = None, launch_attributes: list = None) -> None:
        """Start launch - only if not already started.
        
        Args:
            launch_description: Optional description (will override config if provided)
            launch_attributes: Optional attributes list (will override config if provided)
        """
        if self._launch_started:
            return
            
        if self.rp_launch_manager:
            # Update launch description and attributes if provided
            if launch_description is not None:
                self.rp_launch_manager.launch_description = launch_description
            if launch_attributes is not None:
                self.rp_launch_manager.launch_attributes = self.rp_launch_manager._normalize_attributes(launch_attributes)
            
            self.rp_launch_manager.start_launch()
            self._launch_started = True

    def start_feature(self, feature_name: str, description: str = "", tags: list = None, launch_attributes: list = None) -> None:
        """Start a feature (test suite) in ReportPortal with advanced tag support.

        Args:
            feature_name: Name of the feature to start
            description: Optional description for the feature
            tags: List of Behave tags (supports @attribute, @test_case_id, etc.)
            launch_attributes: Launch attributes (browser_type, scenario_count, version, sprint, environment)
        """
        self.logger.info(f"[RP DEBUG] start_feature called: feature_name={feature_name}, _launch_started={self._launch_started}, launch_id={self.launch_id}")
        
        # Lazy launch start: If launch hasn't started yet, start it now with feature info
        if not self._launch_started:
            self.logger.info(f"Starting launch lazily for feature: {feature_name}")
            # Auto-generate launch_description from first feature if not in config
            launch_description = self._launch_settings.get("launch_description")
            self.logger.info(f"[RP DEBUG] launch_description from config: {launch_description}")
            self.logger.info(f"[RP DEBUG] description parameter: {repr(description)}, type: {type(description)}")
            
            if not launch_description:
                # Use feature description if available, otherwise use feature name
                if description:
                    # Handle both string and list descriptions
                    desc_text = '\n'.join(description) if isinstance(description, list) else description
                    self.logger.info(f"[RP DEBUG] Processed description text: {repr(desc_text[:100])}")
                    # Use feature description directly, without "Test execution for:" prefix
                    launch_description = desc_text if desc_text.strip() else feature_name
                else:
                    # If no description, use feature name
                    self.logger.info(f"[RP DEBUG] No description provided, using feature_name: {feature_name}")
                    launch_description = feature_name
            
            self.logger.info(f"[RP DEBUG] Final launch_description: {repr(launch_description[:100])}")
            
            # Use provided launch_attributes or auto-generate from first feature tags if not in config
            if launch_attributes is None:
                launch_attributes = self._launch_settings.get("launch_attributes", [])
                if not launch_attributes and tags:
                    from .report_portal.rp_utils import RPUtils
                    parsed_tags = RPUtils.parse_behave_tags(tags)
                    launch_attributes = parsed_tags.get('attributes', [])
                    self.logger.info(f"Auto-generated launch_attributes from first feature tags: {len(launch_attributes)} attributes")
            else:
                self.logger.info(f"Using provided launch_attributes: {len(launch_attributes)} attributes")
            
            # Set launch name from feature name (per requirements)
            launch_name = feature_name
            self.logger.info(f"[RP DEBUG] Launch name set to feature name: {launch_name}")

            # Update launch name in launch coordinator if available
            if self.rp_launch_manager:
                self.rp_launch_manager.update_launch_name(launch_name)

            self.logger.info(f"Calling start_launch with name='{launch_name}', description='{launch_description[:50]}...', attributes={len(launch_attributes)}")
            self.start_launch(launch_description=launch_description, launch_attributes=launch_attributes)
            self.logger.info(f"Launch started successfully. Launch ID: {self.launch_id}")
        
        if self.rp_feature_manager:
            # Ensure description is properly formatted (handle both string and list)
            desc_text = '\n'.join(description) if isinstance(description, list) else (description or "")
            self.logger.info(f"[RP DEBUG] Starting feature in RP: name={feature_name}, description length={len(desc_text)}, tags={tags}")
            self.rp_feature_manager.start_feature(feature_name, desc_text, tags)

    def finish_feature(self, status: str = "PASSED") -> None:
        """Finish a feature (test suite) in ReportPortal.
        
        Args:
            status: Final status of the feature (PASSED, FAILED, etc.)
        """
        if self.rp_feature_manager:
            self.rp_feature_manager.finish_feature(status)

    def start_test(self, name: str, test_type: str = "TEST", tags: list = None, description: str = "") -> None:
        """Start a test (scenario) in ReportPortal with advanced tag support.

        Args:
            name: Name of the test/scenario to start
            test_type: Type of test item (SCENARIO, TEST, etc.)
            tags: List of Behave tags (supports @attribute, @test_case_id, etc.)
            description: Optional scenario description
        """
        if self.rp_test_manager:
            self.rp_test_manager.start_test(name, test_type, tags, description)

    def start_step(self, step_name: str, tags: list = None) -> None:
        """Start a step within a test in ReportPortal.
        
        Args:
            step_name: Name of the step to start
        """
        if self.rp_step_manager:
            self.rp_step_manager.start_step(step_name, tags)

    def finish_step(self, status: str) -> None:
        """Finish a step in ReportPortal.
        
        Args:
            status: Final status of the step (PASSED, FAILED, etc.)
        """
        if self.rp_step_manager:
            self.rp_step_manager.finish_step(status)

    def finish_test(self, status: str, attributes: list = None) -> None:
        """Finish a test (scenario) in ReportPortal with optional attributes.

        Args:
            status: Final status of the test (PASSED, FAILED, etc.)
            attributes: Optional list of attributes (e.g., performance metrics)
        """
        if self.rp_test_manager:
            self.rp_test_manager.finish_test(status, attributes)

    def finish_launch(self, status: str = "FINISHED", launch_id: str | None = None) -> None:
        """Finish a launch in ReportPortal.
        
        Args:
            status: Final status of the launch (FINISHED, FAILED, etc.)
            launch_id: Optional launch ID to finish (uses current launch if not provided)
        """
        if self.rp_launch_manager:
            # If launch_id provided, use it; otherwise use the one from launch_manager
            target_launch_id = launch_id or self.launch_id
            # Store launch_id before finishing (it will be cleared after finish)
            if target_launch_id:
                self._finished_launch_id = target_launch_id
            self.rp_launch_manager.finish_launch(status, target_launch_id)

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log a message to ReportPortal.

        Args:
            message: Message text to log
            level: Log level (INFO, DEBUG, WARN, ERROR, etc.)
        """
        if self.rp_logger:
            self.rp_logger.log_message(message, level)
        else:
            self.logger.warning(f"RP logger not available, cannot log message: {message[:50]}...")

    def log_metadata(self, key: str, value: str, level: str = "INFO") -> None:
        """Log custom metadata to current test item in ReportPortal.

        Formats metadata as key-value pair for better visibility in ReportPortal.
        Useful for runtime metadata enrichment (environment details, test data IDs, etc.).

        Args:
            key: Metadata key (e.g., "environment", "browser_version", "test_user")
            value: Metadata value
            level: Log level (default: INFO)

        Example:
            >>> rp_client.log_metadata("browser_version", "Chrome 120")
            >>> rp_client.log_metadata("test_data_id", "USER-12345", "DEBUG")
        """
        if self.rp_logger:
            self.rp_logger.log_metadata(key, value, level)

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

    def attach_file(self, file_data, description: str = "", attachment_type: str = "") -> None:
        """Attach a file to the current test item in ReportPortal.

        Args:
            file_data: File data as bytes or Path to the file to attach
            description: Optional description for the attachment
            attachment_type: Optional type of attachment (screenshot, video, etc.)
        """
        if self.rp_attachment_manager:
            self.rp_attachment_manager.attach_file(file_data, description, attachment_type)

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
        # Return finished launch_id if launch is finished, otherwise return active launch_id
        if hasattr(self, '_finished_launch_id') and self._finished_launch_id:
            return self._finished_launch_id
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

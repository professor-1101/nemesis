"""Reporter management with config-driven architecture."""
import traceback
from typing import Optional, Any

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.reporting.local import LocalReporter
from nemesis.reporting.reportportal import ReportPortalClient


class ReporterManager:
    """Manages all reporters with config-driven initialization."""

    def __init__(self, config: ConfigLoader, execution_manager: Optional[Any] = None, skip_rp_init: bool = False):
        """Initialize reporter manager.

        Args:
            config: Centralized config loader
            execution_manager: Execution manager (optional, only for local)
            skip_rp_init: If True, skip ReportPortal initialization (for finalization phase)
        """
        self.logger = Logger.get_instance({})
        self.config = config
        self.execution_manager = execution_manager
        self.skip_rp_init = skip_rp_init

        self.local_reporter = None
        self.rp_client = None

        self._initialize_reporters()

    def _initialize_reporters(self) -> None:
        """Initialize enabled reporters with graceful degradation."""
        # Initialize local reporter
        if self.config.get("reporting.local.enabled", True):
            if self.execution_manager:
                try:
                    execution_id = self.execution_manager.get_execution_id()
                    execution_path = self.execution_manager.get_execution_path()

                    self.local_reporter = LocalReporter(
                        execution_id,
                        execution_path
                    )
                    self.logger.info(f"Local reporter initialized with execution_id: {execution_id}")
                except (AttributeError, RuntimeError, OSError, IOError) as e:
                    # Local reporter initialization errors
                    self.logger.error(f"Local reporter init failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReporterManager", method="_initialize_reporters")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from LocalReporter initialization
                    # NOTE: LocalReporter may raise various exceptions we cannot predict
                    self.logger.error(f"Local reporter init failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReporterManager", method="_initialize_reporters")
            else:
                self.logger.warning("Local reporting enabled but no execution manager available")

        # Initialize ReportPortal
        # IMPORTANT: Skip initialization if skip_rp_init flag is set OR no execution_manager (finalization phase)
        # ReportPortal should have been initialized in before_all hook
        if self.config.get("reporting.reportportal.enabled", False):
            if self.skip_rp_init or not self.execution_manager:
                # We're in finalization phase - ReportPortal was already initialized
                # Try to get existing client from EnvironmentManager first
                self.logger.info("Skipping ReportPortal initialization in finalization - will use existing client")
                try:
                    from nemesis.infrastructure.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                    env_manager = _get_env_manager()
                    if env_manager and hasattr(env_manager, 'reporting_env') and env_manager.reporting_env.report_manager:
                        existing_rp_client = env_manager.reporting_env.report_manager.reporter_manager.get_rp_client()
                        if existing_rp_client:
                            self.rp_client = existing_rp_client
                            self.logger.info("Using existing ReportPortal client from EnvironmentManager")
                            return
                except (ImportError, AttributeError) as e:
                    # Non-critical: failed to get existing ReportPortal client from EnvironmentManager
                    self.logger.debug(f"Could not get existing ReportPortal client - import/attribute error: {e}", module=__name__, class_name="ReporterManager", method="_initialize_reporters")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from EnvironmentManager access
                    # NOTE: EnvironmentManager import or access may raise various exceptions
                    self.logger.debug(f"Could not get existing ReportPortal client: {e}", module=__name__, class_name="ReporterManager", method="_initialize_reporters")

                # If EnvironmentManager doesn't have the client (cross-process), create new client
                # but it will reuse saved launch_id from file (handled in ReportPortalClient.__init__)
                try:
                    self.logger.info("Creating new ReportPortalClient for finalization (will reuse saved launch_id)")
                    self.rp_client = ReportPortalClient(self.config)
                    if self.rp_client.launch_id:
                        self.logger.info(f"ReportPortal client initialized with saved launch_id: {self.rp_client.launch_id}")
                    else:
                        self.logger.warning("ReportPortal client created but no launch_id found")
                        self.rp_client = None
                except (AttributeError, RuntimeError, ImportError) as e:
                    # ReportPortal client initialization errors
                    self.logger.warning(f"Failed to create ReportPortal client for finalization: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReporterManager", method="_initialize_reporters")
                    self.rp_client = None
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from ReportPortalClient initialization
                    # NOTE: ReportPortalClient may raise various exceptions we cannot predict
                    self.logger.warning(f"Failed to create ReportPortal client for finalization: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReporterManager", method="_initialize_reporters")
                    self.rp_client = None
                return

            try:
                self.rp_client = ReportPortalClient(self.config)

                if self.rp_client.launch_id:
                    self.logger.info(
                        f"ReportPortal initialized - Launch: {self.rp_client.launch_id}"
                    )

                    launch_url = self.rp_client.get_launch_url()
                    if launch_url:
                        self.logger.info(f"ReportPortal URL: {launch_url}")
                else:
                    raise RuntimeError("Launch ID not obtained")

            except (AttributeError, RuntimeError, ImportError) as e:
                # ReportPortal initialization errors
                self.logger.error(f"ReportPortal init failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReporterManager", method="_initialize_reporters")
                self.logger.warning("Continuing without ReportPortal")
                self.rp_client = None
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortalClient initialization
                # NOTE: ReportPortalClient may raise various exceptions we cannot predict
                self.logger.error(f"ReportPortal init failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReporterManager", method="_initialize_reporters")
                self.logger.warning("Continuing without ReportPortal")
                self.rp_client = None

    def get_local_reporter(self) -> Optional[LocalReporter]:
        """Get local reporter."""
        return self.local_reporter

    def get_rp_client(self) -> Optional[ReportPortalClient]:
        """Get ReportPortal client."""
        return self.rp_client

    def is_local_enabled(self) -> bool:
        """Check if local reporting is enabled and active."""
        return self.config.get("reporting.local.enabled", True) and self.local_reporter is not None

    def is_rp_enabled(self) -> bool:
        """Check if ReportPortal is enabled and active."""
        return self.config.get("reporting.reportportal.enabled", False) and self.rp_client is not None

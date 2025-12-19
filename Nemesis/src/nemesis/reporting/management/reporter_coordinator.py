"""Reporter management with config-driven architecture."""
from typing import Optional, Any

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.reporting.local import LocalReporter
from nemesis.reporting.reportportal import ReportPortalClient
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class ReporterCoordinator:
    """Coordinates all reporters with config-driven initialization."""

    def __init__(self, config: ConfigLoader, execution_manager: Optional[Any] = None, skip_rp_init: bool = False):
        """Initialize reporter coordinator.

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

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError, OSError, IOError, Exception),
        specific_message="Local reporter init failed: {error}",
        fallback_message="Local reporter init failed: {error}",
        return_on_error=None
    )
    def _init_local_reporter(self) -> Optional[LocalReporter]:
        """Initialize local reporter with exception handling."""
        execution_id = self.execution_manager.get_execution_id()
        execution_path = self.execution_manager.get_execution_path()

        reporter = LocalReporter(execution_id, execution_path)
        self.logger.info(f"Local reporter initialized with execution_id: {execution_id}")
        return reporter

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(ImportError, AttributeError, Exception),
        specific_message="Could not get existing ReportPortal client: {error}",
        fallback_message="Could not get existing ReportPortal client: {error}",
        return_on_error=None
    )
    def _get_existing_rp_client(self) -> Optional[ReportPortalClient]:
        """Get existing RP client from EnvironmentCoordinator."""
        from nemesis.infrastructure.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
        env_manager = _get_env_manager()
        if env_manager and hasattr(env_manager, 'reporting_env') and env_manager.reporting_env.report_manager:
            existing_rp_client = env_manager.reporting_env.report_manager.reporter_manager.get_rp_client()
            if existing_rp_client:
                self.logger.info("Using existing ReportPortal client from EnvironmentCoordinator")
                return existing_rp_client
        return None

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError, ImportError, Exception),
        specific_message="Failed to create ReportPortal client for finalization: {error}",
        fallback_message="Failed to create ReportPortal client for finalization: {error}",
        return_on_error=None
    )
    def _create_rp_client_for_finalization(self) -> Optional[ReportPortalClient]:
        """Create new RP client for finalization phase."""
        self.logger.info("Creating new ReportPortalClient for finalization (will reuse saved launch_id)")
        client = ReportPortalClient(self.config)
        if client.launch_id:
            self.logger.info(f"ReportPortal client initialized with saved launch_id: {client.launch_id}")
            return client
        else:
            self.logger.warning("ReportPortal client created but no launch_id found")
            return None

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError, ImportError, Exception),
        specific_message="ReportPortal init failed: {error}",
        fallback_message="ReportPortal init failed: {error}",
        return_on_error=None
    )
    def _init_rp_client(self) -> Optional[ReportPortalClient]:
        """Initialize ReportPortal client with exception handling."""
        client = ReportPortalClient(self.config)

        if client.launch_id:
            self.logger.info(f"ReportPortal initialized - Launch: {client.launch_id}")

            launch_url = client.get_launch_url()
            if launch_url:
                self.logger.info(f"ReportPortal URL: {launch_url}")
            return client
        else:
            raise RuntimeError("Launch ID not obtained")

    def _initialize_reporters(self) -> None:
        """Initialize enabled reporters with graceful degradation."""
        # Initialize local reporter
        if self.config.get("reporting.local.enabled", True):
            if self.execution_manager:
                self.local_reporter = self._init_local_reporter()
            else:
                self.logger.warning("Local reporting enabled but no execution manager available")

        # Initialize ReportPortal
        # IMPORTANT: Skip initialization if skip_rp_init flag is set OR no execution_manager (finalization phase)
        # ReportPortal should have been initialized in before_all hook
        if self.config.get("reporting.reportportal.enabled", False):
            if self.skip_rp_init or not self.execution_manager:
                # We're in finalization phase - ReportPortal was already initialized
                # Try to get existing client from EnvironmentCoordinator first
                self.logger.info("Skipping ReportPortal initialization in finalization - will use existing client")

                existing_client = self._get_existing_rp_client()
                if existing_client:
                    self.rp_client = existing_client
                    return

                # If EnvironmentCoordinator doesn't have the client (cross-process), create new client
                # but it will reuse saved launch_id from file (handled in ReportPortalClient.__init__)
                self.rp_client = self._create_rp_client_for_finalization()
                return

            self.rp_client = self._init_rp_client()
            if not self.rp_client:
                self.logger.warning("Continuing without ReportPortal")

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

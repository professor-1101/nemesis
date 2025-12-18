"""Centralized environment manager for Nemesis framework."""
import os
from typing import Any, Optional
from pathlib import Path

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.shared.execution_context import ExecutionContext
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback
from .browser_environment import BrowserEnvironment
from .reporting_environment import ReportingEnvironment
from .logger_environment import LoggerEnvironment


class EnvironmentCoordinator:
    """Centralized environment manager for test setup and teardown."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize environment manager.

        Args:
            config_dir: Path to configuration directory
        """
        self.config = ConfigLoader(config_dir)
        self.logger = Logger.get_instance({})

        # Initialize sub-environments
        self.browser_env = BrowserEnvironment(self.config)
        self.reporting_env = ReportingEnvironment(self.config)
        self.logger_env = LoggerEnvironment(self.config)

        self.initialized = False
        self.execution_id: Optional[str] = None
        self.rp_launch_id: Optional[str] = None  # Store ReportPortal launch_id for cross-process access

    @handle_exceptions_with_fallback(
        log_level="critical",
        specific_exceptions=(AttributeError, RuntimeError, ImportError),
        specific_message="Critical error in environment setup: {error}",
        fallback_message="Critical error in environment setup: {error}",
        return_on_error=True
    )
    def setup_environment(self, context: Any) -> bool:
        """Setup complete test environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        self.logger.info("Setting up Nemesis test environment...")

        # Mark as initialized early to ensure graceful degradation on errors
        # (decorator will return True on error, but we want initialized=True regardless)
        self.initialized = True

        # Generate execution ID and ensure it's consistent
        self.execution_id = ExecutionContext.get_execution_id()
        context.execution_id = self.execution_id

        # Ensure execution ID is propagated to environment
        os.environ['NEMESIS_EXECUTION_ID'] = self.execution_id

        # Step definitions are handled by Behave automatically
        # Nemesis is completely isolated from project-specific code

        # Setup logger first (non-blocking)
        if not self.logger_env.setup(context):
            self.logger.warning("Logger setup failed, continuing with fallback")

        # Setup browser environment (non-blocking, lazy initialization)
        if not self.browser_env.setup(context):
            self.logger.warning("Browser environment setup failed, will retry on-demand")
            # Don't return False here - allow graceful fallback

        # Setup reporting environment (non-blocking)
        if not self.reporting_env.setup(context):
            self.logger.warning("Reporting setup failed, continuing without reporting")

        # Start test suite (non-blocking)
        self._start_test_suite(context)

        self.logger.info("Nemesis environment setup completed successfully")
        return True

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error during report finalization: {error}",
        fallback_message="Error during report finalization: {error}"
    )
    def _finalize_reports(self) -> None:
        """Finalize reports before teardown.

        This ensures launch_id is accessible from report_manager
        while context is still available.
        """
        if self.reporting_env.report_manager:
            self.logger.info("Finalizing reports in after_all hook...")
            Logger.get_instance({}).info("[DEBUG] EnvironmentCoordinator: Calling report_manager.finalize()")
            self.reporting_env.report_manager.finalize()

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error during environment teardown: {error}",
        fallback_message="Error during environment teardown: {error}"
    )
    def teardown_environment(self, context: Any, status: str = "completed") -> None:
        """Teardown test environment.

        Args:
            context: Behave context object
            status: Test execution status
        """
        self.logger.info(f"Tearing down Nemesis environment (status: {status})")

        # End test suite
        self._end_test_suite(context, status)

        # Finalize reports BEFORE teardown (while context and report_manager are still available)
        self.logger.info(f"Checking report_manager: {self.reporting_env.report_manager is not None}")
        Logger.get_instance({}).info(f"[DEBUG] EnvironmentCoordinator: Checking report_manager: {self.reporting_env.report_manager is not None}")
        self._finalize_reports()

        # Teardown in reverse order
        self.reporting_env.teardown(context, status)
        self.browser_env.teardown(context, status)
        self.logger_env.teardown(context, status)

        self.initialized = False
        self.logger.info("Nemesis environment teardown completed")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error starting test suite: {error}",
        fallback_message="Error starting test suite: {error}"
    )
    def _start_test_suite(self, context: Any) -> None:
        """Start test suite reporting."""
        # Start correlation tracking
        context.correlation_id = self.logger_env.start_correlation(context)

        # Log test suite start
        self.logger_env.log_test_suite_start(context)

        # Start reporting
        self.reporting_env.start_test_suite(context)

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error ending test suite: {error}",
        fallback_message="Error ending test suite: {error}"
    )
    def _end_test_suite(self, context: Any, status: str) -> None:
        """End test suite reporting."""
        # End reporting
        self.reporting_env.end_test_suite(context, status)

        # Log test suite end
        self.logger_env.log_test_suite_end(context, status)

    def get_browser_manager(self) -> Any:
        """Get browser manager instance."""
        return self.browser_env.get_browser_manager()

    def get_report_manager(self) -> Any:
        """Get report manager instance."""
        return self.reporting_env.get_report_manager()

    # Step discovery removed - Behave handles this automatically
    # Nemesis is now completely isolated from project-specific step definitions

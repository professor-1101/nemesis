"""Centralized environment manager for Nemesis framework."""
import os
import traceback
from typing import Any, Optional
from pathlib import Path

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.shared.execution_context import ExecutionContext
from .browser_environment import BrowserEnvironment
from .reporting_environment import ReportingEnvironment
from .logger_environment import LoggerEnvironment


class EnvironmentManager:
    """Centralized environment manager for test setup and teardown."""

    def __init__(self, config_dir: Optional[Path] = None):
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

    def setup_environment(self, context: Any) -> bool:
        """Setup complete test environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.logger.info("Setting up Nemesis test environment...")

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

            self.initialized = True
            self.logger.info("Nemesis environment setup completed successfully")
            return True

        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # Always re-raise these to allow proper program termination
            # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
            raise
        except (AttributeError, RuntimeError, ImportError) as e:
            # Environment setup errors - allow graceful degradation
            self.logger.critical(f"Critical error in environment setup: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="setup_environment")
            # Don't fail completely - allow graceful degradation
            self.initialized = True
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from config or environment setup
            # NOTE: ConfigLoader and sub-environments may raise various exceptions we cannot predict
            self.logger.critical(f"Critical error in environment setup: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="setup_environment")
            # Don't fail completely - allow graceful degradation
            self.initialized = True
            return True

    def teardown_environment(self, context: Any, status: str = "completed") -> None:
        """Teardown test environment.

        Args:
            context: Behave context object
            status: Test execution status
        """
        try:
            self.logger.info(f"Tearing down Nemesis environment (status: {status})")

            # End test suite
            self._end_test_suite(context, status)

            # Finalize reports BEFORE teardown (while context and report_manager are still available)
            # This ensures launch_id is accessible from context.report_manager
            self.logger.info(f"Checking report_manager: {self.reporting_env.report_manager is not None}")
            print(f"[DEBUG] EnvironmentManager: Checking report_manager: {self.reporting_env.report_manager is not None}")
            
            if self.reporting_env.report_manager:
                try:
                    self.logger.info("Finalizing reports in after_all hook...")
                    print("[DEBUG] EnvironmentManager: Calling report_manager.finalize()")
                    self.reporting_env.report_manager.finalize()
                except KeyboardInterrupt:
                    raise
                except SystemExit:
                    raise
                except (AttributeError, RuntimeError) as finalize_error:
                    # Report finalization errors
                    self.logger.error(f"Error during report finalization: {finalize_error}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="teardown_environment")
                except Exception as finalize_error:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from report finalization
                    # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                    self.logger.error(f"Error during report finalization: {finalize_error}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="teardown_environment")

            # Teardown in reverse order
            self.reporting_env.teardown(context, status)
            self.browser_env.teardown(context, status)
            self.logger_env.teardown(context, status)

            self.initialized = False
            self.logger.info("Nemesis environment teardown completed")

        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except (AttributeError, RuntimeError) as e:
            # Environment teardown errors
            self.logger.error(f"Error during environment teardown: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="teardown_environment")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from teardown operations
            # NOTE: Teardown operations may raise various exceptions we cannot predict
            self.logger.error(f"Error during environment teardown: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="teardown_environment")

    def _start_test_suite(self, context: Any) -> None:
        """Start test suite reporting."""
        try:
            # Start correlation tracking
            context.correlation_id = self.logger_env.start_correlation(context)

            # Log test suite start
            self.logger_env.log_test_suite_start(context)

            # Start reporting
            self.reporting_env.start_test_suite(context)

        except (AttributeError, RuntimeError) as e:
            # Test suite start errors - log but continue
            self.logger.warning(f"Error starting test suite: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="_start_test_suite")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from reporting setup
            # NOTE: Reporting environment may raise various exceptions we cannot predict
            self.logger.warning(f"Error starting test suite: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="_start_test_suite")

    def _end_test_suite(self, context: Any, status: str) -> None:
        """End test suite reporting."""
        try:
            # End reporting
            self.reporting_env.end_test_suite(context, status)

            # Log test suite end
            self.logger_env.log_test_suite_end(context, status)

        except (AttributeError, RuntimeError) as e:
            # Test suite end errors - log but continue
            self.logger.warning(f"Error ending test suite: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="_end_test_suite")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from reporting teardown
            # NOTE: Reporting environment may raise various exceptions we cannot predict
            self.logger.warning(f"Error ending test suite: {e}", traceback=traceback.format_exc(), module=__name__, class_name="EnvironmentManager", method="_end_test_suite")

    def get_browser_manager(self) -> Any:
        """Get browser manager instance."""
        return self.browser_env.get_browser_manager()

    def get_report_manager(self) -> Any:
        """Get report manager instance."""
        return self.reporting_env.get_report_manager()

    # Step discovery removed - Behave handles this automatically
    # Nemesis is now completely isolated from project-specific step definitions

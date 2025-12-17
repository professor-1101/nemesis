"""Browser environment management for Nemesis framework."""
import traceback
from typing import Any, Optional

from nemesis.core.config import ConfigLoader
from nemesis.core.execution_context import ExecutionContext
from nemesis.core.logging import Logger
from nemesis.core.browser import BrowserManager
from nemesis.infrastructure.collectors.console import ConsoleCollector
from nemesis.infrastructure.collectors.network import NetworkCollector
from nemesis.infrastructure.collectors.performance import PerformanceCollector


class BrowserEnvironment:
    """Manages browser setup and lifecycle."""

    def __init__(self, config: ConfigLoader):
        """Initialize browser environment.

        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.logger = Logger.get_instance({})
        self.browser_manager: Optional[BrowserManager] = None
        self.collectors = {}

    def setup(self, context: Any) -> bool:
        """Setup browser environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.logger.info("Setting up browser environment...")

            # Initialize browser manager
            self.browser_manager = BrowserManager(self.config)
            context.browser_manager = self.browser_manager

            # Browser will be started in before_scenario, not here
            # This prevents timing conflicts with step discovery
            context.browser_crashed = False

            # Initialize collectors (will be activated per scenario)
            self._initialize_collectors(context)

            self.logger.info("Browser environment setup completed")
            return True

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError, ImportError) as e:
            # Browser manager initialization errors
            self.logger.error(f"Browser environment setup failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="setup")
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from BrowserManager or collectors
            # NOTE: BrowserManager may raise various exceptions we cannot predict
            self.logger.error(f"Browser environment setup failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="setup")
            return False

    def teardown(self, _context: Any, _status: str) -> None:
        """Teardown browser environment.

        Args:
            context: Behave context object
            status: Test execution status
        """
        try:
            self.logger.info("Tearing down browser environment...")

            # Stop collectors
            self._stop_collectors()

            # Close browser
            if self.browser_manager:
                self.browser_manager.stop()

            self.logger.info("Browser environment teardown completed")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (RuntimeError, AttributeError) as e:
            # Browser cleanup errors - log but don't fail
            self.logger.error(f"Error during browser teardown: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="teardown")

    def start_browser_for_scenario(self, context: Any, scenario: Any) -> bool:
        """Start browser for specific scenario.

        Args:
            context: Behave context object
            scenario: Behave scenario object (can be step object for lazy initialization)

        Returns:
            True if browser started successfully
        """
        try:
            if not self.browser_manager:
                self.logger.error("Browser manager not initialized")
                return False

            # Check if browser is already started
            if getattr(context, 'browser_started', False):
                self.logger.debug("Browser already started, skipping startup")
                return True

            # Start browser and get page
            execution_id = getattr(context, 'execution_id', None)
            if not execution_id:
                execution_id = ExecutionContext.get_execution_id()
                context.execution_id = execution_id

            # Start browser with error handling
            try:
                self.logger.info(f"Starting browser with execution_id: {execution_id}")
                print(f"DEBUG: Starting browser with execution_id: {execution_id}")

                # Check if browser manager is properly initialized
                if not self.browser_manager:
                    self.logger.error("Browser manager is None")
                    print("DEBUG: Browser manager is None")
                    context.browser_crashed = True
                    return False

                print("DEBUG: Browser manager is available, calling start()")
                context.page = self.browser_manager.start(execution_id)
                print("DEBUG: Browser started successfully, getting browser instance")
                context.browser = self.browser_manager.get_browser()

                # Mark browser as started
                context.browser_started = True
                context.browser_crashed = False

                # Activate collectors for this scenario
                self._activate_collectors(context)

                scenario_name = getattr(scenario, 'name', 'unknown')
                self.logger.info(f"Browser started for scenario: {scenario_name}")
                print(f"DEBUG: Browser started for scenario: {scenario_name}")
                return True

            except (KeyboardInterrupt, SystemExit):
                # Always re-raise these to allow proper program termination
                raise
            except (RuntimeError, AttributeError) as browser_error:
                # BrowserManager or Playwright API errors
                self.logger.error(f"Browser startup failed: {browser_error}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="start_browser_for_scenario")
                print(f"DEBUG: Browser startup failed: {browser_error}")
                # Don't mark as crashed immediately, allow graceful fallback
                context.browser_crashed = True
                return False
            except Exception as browser_error:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from BrowserManager
                # NOTE: BrowserManager.start() may raise various exceptions we cannot predict
                self.logger.error(f"Browser startup failed: {browser_error}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="start_browser_for_scenario")
                print(f"DEBUG: Browser startup failed: {browser_error}")
                # Don't mark as crashed immediately, allow graceful fallback
                context.browser_crashed = True
                return False

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Browser manager or execution context errors
            self.logger.error(f"Failed to start browser for scenario: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="start_browser_for_scenario")
            # Mark browser as crashed
            context.browser_crashed = True
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from BrowserManager
            # NOTE: BrowserManager.start() may raise various exceptions we cannot predict
            self.logger.error(f"Failed to start browser for scenario: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="start_browser_for_scenario")
            # Mark browser as crashed
            context.browser_crashed = True
            return False

    def stop_browser_for_scenario(self, context: Any, scenario: Any, status: str) -> None:
        """Stop browser for specific scenario.

        Args:
            context: Behave context object
            scenario: Behave scenario object
            status: Scenario execution status
        """
        try:
            # Only stop browser if it was actually started
            if getattr(context, 'browser_started', False):
                # Stop collectors
                self._stop_collectors()

                # Stop browser
                if self.browser_manager:
                    self.browser_manager.stop()

                # Mark browser as stopped
                context.browser_started = False

                scenario_name = getattr(scenario, 'name', 'unknown')
                self.logger.info(f"Browser stopped for scenario: {scenario_name} (status: {status})")
            else:
                self.logger.debug("Browser was not started, skipping stop")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (RuntimeError, AttributeError) as e:
            # Browser stop errors - log but don't fail
            self.logger.error(f"Error stopping browser for scenario: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="stop_browser_for_scenario")

    def _initialize_collectors(self, context: Any) -> None:
        """Initialize data collectors."""
        try:
            # Collectors will be initialized when browser starts
            context.collectors = {}
            self.logger.debug("Collectors initialized")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Collector initialization errors - log but continue
            self.logger.warning(f"Error initializing collectors: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="_initialize_collectors")

    def _activate_collectors(self, context: Any) -> None:
        """Activate collectors for current scenario."""
        try:
            if not hasattr(context, 'page') or not context.page:
                return

            page = context.page

            # Initialize collectors based on configuration
            if self.config.get("attachments.console.enabled", True):
                context.collectors['console'] = ConsoleCollector(page)

            if self.config.get("attachments.network.enabled", True):
                context.collectors['network'] = NetworkCollector(page)

            if self.config.get("attachments.performance.enabled", True):
                context.collectors['performance'] = PerformanceCollector(page)

            self.logger.debug("Collectors activated for scenario")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError, ImportError) as e:
            # Collector activation errors - log but continue
            self.logger.warning(f"Error activating collectors: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="_activate_collectors")

    def _stop_collectors(self) -> None:
        """Stop all active collectors."""
        try:
            # Collectors will be stopped when browser stops
            self.logger.debug("Collectors stopped")

        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Collector stop errors - log but continue
            self.logger.warning(f"Error stopping collectors: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BrowserEnvironment", method="_stop_collectors")

    def get_browser_manager(self) -> Optional[BrowserManager]:
        """Get browser manager instance."""
        return self.browser_manager

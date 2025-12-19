"""Browser environment management for Nemesis framework."""
from typing import Any, Optional

from nemesis.infrastructure.config import ConfigLoader
from nemesis.shared.execution_context import ExecutionContext
from nemesis.infrastructure.logging import Logger
from nemesis.infrastructure.browser import BrowserService
from nemesis.infrastructure.collectors.console import ConsoleCollector
from nemesis.infrastructure.collectors.network import NetworkCollector
from nemesis.infrastructure.collectors.performance import PerformanceCollector
from nemesis.utils.decorators.exception_handler import handle_exceptions, handle_exceptions_with_fallback


class BrowserEnvironment:
    """Manages browser setup and lifecycle."""

    def __init__(self, config: ConfigLoader) -> None:
        """Initialize browser environment.

        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.logger = Logger.get_instance({})
        self.browser_manager: Optional[BrowserService] = None
        self.collectors = {}

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError, ImportError),
        specific_message="Browser environment setup failed: {error}",
        fallback_message="Browser environment setup failed: {error}",
        return_on_error=False
    )
    def setup(self, context: Any) -> bool:
        """Setup browser environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        self.logger.info("Setting up browser environment...")

        # Initialize browser manager
        self.browser_manager = BrowserService(self.config)
        context.browser_manager = self.browser_manager

        # Browser will be started in before_scenario, not here
        # This prevents timing conflicts with step discovery
        context.browser_crashed = False

        # Initialize collectors (will be activated per scenario)
        self._initialize_collectors(context)

        self.logger.info("Browser environment setup completed")
        return True

    @handle_exceptions(
        log_level="error",
        catch_exceptions=(RuntimeError, AttributeError),
        message_template="Error during browser teardown: {error}"
    )
    def teardown(self, _context: Any, _status: str) -> None:
        """Teardown browser environment.

        Args:
            context: Behave context object
            status: Test execution status
        """
        self.logger.info("Tearing down browser environment...")

        # Stop collectors
        self._stop_collectors()

        # Close browser
        if self.browser_manager:
            self.browser_manager.stop()

        self.logger.info("Browser environment teardown completed")

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(RuntimeError, AttributeError),
        specific_message="Browser startup failed: {error}",
        fallback_message="Browser startup failed: {error}",
        return_on_error=False
    )
    def _start_browser_internal(self, context: Any, execution_id: str, scenario_name: str) -> bool:
        """Internal method to start browser with execution ID.

        Args:
            context: Behave context object
            execution_id: Execution ID for the browser
            scenario_name: Name of the scenario

        Returns:
            True if browser started successfully, False otherwise
        """
        self.logger.info(f"Starting browser with execution_id: {execution_id}")

        # Check if browser manager is properly initialized
        if not self.browser_manager:
            self.logger.debug("Browser manager is None")
            context.browser_crashed = True
            return False

        self.logger.debug("Browser manager is available, calling start()")
        self.logger.debug("Browser started successfully, getting browser instance")
        context.browser = self.browser_manager.get_browser()

        # Mark browser as started
        context.browser_started = True
        context.browser_crashed = False

        # Activate collectors for this scenario
        self._activate_collectors(context)

        self.logger.info(f"Browser started for scenario: {scenario_name}")
        return True

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to start browser for scenario: {error}",
        fallback_message="Failed to start browser for scenario: {error}",
        return_on_error=False
    )
    def start_browser_for_scenario(self, context: Any, scenario: Any) -> bool:
        """Start browser for specific scenario.

        Args:
            context: Behave context object
            scenario: Behave scenario object (can be step object for lazy initialization)

        Returns:
            True if browser started successfully
        """
        # Get scenario name early (fixes undefined variable bug)
        scenario_name = getattr(scenario, 'name', 'unknown')

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

        # Start browser with error handling via helper method
        success = self._start_browser_internal(context, execution_id, scenario_name)
        if not success:
            context.browser_crashed = True

        return success

    @handle_exceptions(
        log_level="error",
        catch_exceptions=(RuntimeError, AttributeError),
        message_template="Error stopping browser for scenario: {error}"
    )
    def stop_browser_for_scenario(self, context: Any, scenario: Any, status: str) -> None:
        """Stop browser for specific scenario.

        Args:
            context: Behave context object
            scenario: Behave scenario object
            status: Scenario execution status
        """
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

    @handle_exceptions(
        log_level="warning",
        catch_exceptions=(AttributeError, RuntimeError),
        message_template="Error initializing collectors: {error}"
    )
    def _initialize_collectors(self, context: Any) -> None:
        """Initialize data collectors."""
        # Collectors will be initialized when browser starts
        context.collectors = {}
        self.logger.debug("Collectors initialized")

    @handle_exceptions(
        log_level="warning",
        catch_exceptions=(AttributeError, RuntimeError, ImportError),
        message_template="Error activating collectors: {error}"
    )
    def _activate_collectors(self, context: Any) -> None:
        """Activate collectors for current scenario."""
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

    @handle_exceptions(
        log_level="warning",
        catch_exceptions=(AttributeError, RuntimeError),
        message_template="Error stopping collectors: {error}"
    )
    def _stop_collectors(self) -> None:
        """Stop all active collectors."""
        # Collectors will be stopped when browser stops
        self.logger.debug("Collectors stopped")

    def get_browser_manager(self) -> Optional[BrowserService]:
        """Get browser manager instance."""
        return self.browser_manager

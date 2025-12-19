"""Logger environment management for Nemesis framework."""
import uuid
from typing import Any, Optional

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class LoggerEnvironment:
    """Manages logger setup and lifecycle."""

    def __init__(self, config: ConfigLoader) -> None:
        """Initialize logger environment.

        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.logger: Optional[Logger] = None
        self.correlation_id: Optional[str] = None

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError, ImportError),
        specific_message="Logger setup failed: {error}",
        fallback_message="Logger setup failed: {error}",
        return_on_error=False
    )
    def setup(self, context: Any) -> bool:
        """Setup logger environment.

        Args:
            context: Behave context object

        Returns:
            True if setup successful, False otherwise
        """
        # Initialize logger with configuration
        self.logger = Logger.get_instance(self.config.get("logging", {}))
        context.logger = self.logger

        return True

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error during logger teardown: {error}",
        fallback_message="Error during logger teardown: {error}"
    )
    def teardown(self, _context: Any, status: str) -> None:
        """Teardown logger environment.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            status: Test execution status
        """
        if self.logger:
            self.logger.info(f"Logger environment teardown completed (status: {status})")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error starting correlation: {error}",
        fallback_message="Error starting correlation: {error}",
        return_on_error="unknown"
    )
    def start_correlation(self, context: Any) -> str:
        """Start correlation tracking.

        Args:
            context: Behave context object

        Returns:
            Correlation ID
        """
        self.correlation_id = str(uuid.uuid4())[:8]
        context.correlation_id = self.correlation_id

        if self.logger:
            self.logger.info(f"Correlation tracking started: {self.correlation_id}")

        return self.correlation_id

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging test suite start: {error}",
        fallback_message="Error logging test suite start: {error}"
    )
    def log_test_suite_start(self, context: Any) -> None:
        """Log test suite start.

        Args:
            context: Behave context object
        """
        if self.logger:
            self.logger.info("=" * 60)
            self.logger.info("TEST SUITE STARTED")
            self.logger.info(f"Execution ID: {context.execution_id}")
            self.logger.info(f"Correlation ID: {context.correlation_id}")
            self.logger.info("=" * 60)

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging test suite end: {error}",
        fallback_message="Error logging test suite end: {error}"
    )
    def log_test_suite_end(self, context: Any, status: str) -> None:
        """Log test suite end.

        Args:
            context: Behave context object
            status: Test execution status
        """
        if self.logger:
            self.logger.info("=" * 60)
            self.logger.info("TEST SUITE ENDED")
            self.logger.info(f"Status: {status}")
            self.logger.info(f"Execution ID: {context.execution_id}")
            self.logger.info(f"Correlation ID: {context.correlation_id}")
            self.logger.info("=" * 60)

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging feature start: {error}",
        fallback_message="Error logging feature start: {error}"
    )
    def log_feature_start(self, _context: Any, feature: Any) -> None:
        """Log feature start.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            feature: Behave feature object
        """
        if self.logger:
            self.logger.info(f"Feature started: {feature.name}")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging feature end: {error}",
        fallback_message="Error logging feature end: {error}"
    )
    def log_feature_end(self, _context: Any, feature: Any, status: str) -> None:
        """Log feature end.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            feature: Behave feature object
            status: Feature execution status
        """
        if self.logger:
            self.logger.info(f"Feature ended: {feature.name} (status: {status})")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging scenario start: {error}",
        fallback_message="Error logging scenario start: {error}"
    )
    def log_scenario_start(self, _context: Any, scenario: Any) -> None:
        """Log scenario start.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            scenario: Behave scenario object
        """
        if self.logger:
            self.logger.info(f"Scenario started: {scenario.name}")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging scenario end: {error}",
        fallback_message="Error logging scenario end: {error}"
    )
    def log_scenario_end(self, _context: Any, scenario: Any, status: str) -> None:
        """Log scenario end.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            scenario: Behave scenario object
            status: Scenario execution status
        """
        if self.logger:
            self.logger.info(f"Scenario ended: {scenario.name} (status: {status})")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging step start: {error}",
        fallback_message="Error logging step start: {error}"
    )
    def log_step_start(self, _context: Any, step: Any) -> None:
        """Log step start.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            step: Behave step object
        """
        if self.logger:
            self.logger.debug(f"Step started: {step.step_type} {step.name}")

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Error logging step end: {error}",
        fallback_message="Error logging step end: {error}"
    )
    def log_step_end(self, _context: Any, step: Any, status: str) -> None:
        """Log step end.

        Args:
            _context: Behave context object (unused, kept for interface compatibility)
            step: Behave step object
            status: Step execution status
        """
        if self.logger:
            self.logger.debug(f"Step ended: {step.step_type} {step.name} (status: {status})")

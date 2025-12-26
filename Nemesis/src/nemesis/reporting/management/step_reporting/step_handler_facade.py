"""Step Handler Facade - Main interface for step reporting.

Orchestrates step reporting by delegating to specialized components:
- DataProcessor: Placeholder replacement and metadata extraction
- NetworkReporter: Network activity logging and attachment
- ConsoleReporter: Console logs logging and attachment
- PerformanceReporter: Performance metrics attachment
- CollectorsAccessor: Unified collector data access

This facade maintains backward compatibility with the original StepHandler interface.
"""
from typing import Any, Callable

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback

from .collectors_accessor import CollectorsAccessor
from .data_processor import StepDataProcessor
from .network_formatter import NetworkDataFormatter
from .console_formatter import ConsoleDataFormatter
from .network_reporter import NetworkReporter
from .console_reporter import ConsoleReporter
from .performance_reporter import PerformanceReporter


class StepHandlerFacade:
    """
    Facade for step reporting operations.

    Responsibilities (Single Responsibility Principle):
    - Coordinate step lifecycle (start/end)
    - Delegate to specialized reporters for data logging/attachment
    - Maintain backward compatibility with original interface
    """

    def __init__(self, reporter_manager: Any) -> None:
        """
        Initialize step handler facade.

        Args:
            reporter_manager: Reporter manager instance
        """
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

        # Initialize specialized components
        self.collectors = CollectorsAccessor()
        self.data_processor = StepDataProcessor()

        # Initialize formatters
        self.network_formatter = NetworkDataFormatter()
        self.console_formatter = ConsoleDataFormatter()

        # Initialize reporters with their dependencies
        self.network_reporter = NetworkReporter(self.collectors, self.network_formatter)
        self.console_reporter = ConsoleReporter(self.collectors, self.console_formatter)
        self.performance_reporter = PerformanceReporter(self.collectors)

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to call local reporter: {error}",
        fallback_message="Failed to call local reporter: {error}"
    )
    def _call_local_reporter(self, callback: Callable[[], None]) -> None:
        """Call local reporter method with exception handling."""
        callback()

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to call ReportPortal: {error}",
        fallback_message="Failed to call ReportPortal: {error}"
    )
    def _call_rp_client(self, callback: Callable[[], None]) -> None:
        """Call ReportPortal client method with exception handling."""
        callback()

    def start_step(self, step: Any) -> None:
        """
        Start step reporting.

        Args:
            step: Behave step object
        """
        # Process step name (replace PLACEHOLDER values)
        step_name = self.data_processor.process_step_name(step)

        # Extract metadata
        metadata = self.data_processor.extract_metadata(step)
        feature_name = metadata["feature_name"]
        scenario_name = metadata["scenario_name"]
        code_ref = metadata["code_ref"]

        self.logger.step_start(step_name)

        # Update environment context for attachment naming
        try:
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()
            if env_manager:
                env_manager.set_current_step(step_name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass  # Non-critical

        # ReportPortal reporting
        if self.reporter_manager.is_rp_enabled():
            # Create tags with feature, scenario, and code_ref info
            tags = []
            if feature_name:
                tags.append(f"@feature:{feature_name}")
            if scenario_name:
                tags.append(f"@scenario:{scenario_name}")
            if code_ref:
                tags.append(f"@code_ref:{code_ref}")

            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().start_step(step_name, tags)
            )

        # Local reporting
        if self.reporter_manager.is_local_enabled():
            def _start_local():
                self.reporter_manager.get_local_reporter().start_step(step)
                self.reporter_manager.get_local_reporter().add_log(f"Step started: {step_name}", "INFO")
            self._call_local_reporter(_start_local)

    def end_step(self, step: Any, duration: float = 0.0) -> None:
        """
        End step reporting.

        Args:
            step: Behave step object
            duration: Step duration in seconds
        """
        step_name = getattr(step, 'name', str(step))
        status = getattr(step, 'status', None)

        # Determine status string
        if hasattr(status, 'name'):
            if status.name == "passed":
                status_str = "PASSED"
            elif status.name == "failed":
                status_str = "FAILED"
            elif status.name == "skipped":
                status_str = "SKIPPED"
            else:
                status_str = "PASSED"  # Default fallback
        else:
            status_str = "PASSED"

        # Convert duration to milliseconds
        try:
            duration_float = float(duration) if duration else 0.0
            duration_ms = int(duration_float * 1000) if duration_float > 0 else 0
        except (ValueError, TypeError):
            duration_ms = 0

        self.logger.step_end(step_name, status_str, duration_ms)

        # Local reporting
        if self.reporter_manager.is_local_enabled():
            def _end_local():
                self.reporter_manager.get_local_reporter().end_step(step, status_str)
                self.reporter_manager.get_local_reporter().add_log(
                    f"Step ended: {step_name} - Status: {status_str} - Duration: {duration_ms}ms",
                    "INFO"
                )
            self._call_local_reporter(_end_local)

        # ReportPortal reporting
        if self.reporter_manager.is_rp_enabled():
            # Log execution details
            def _log_execution_details():
                execution_log = f"Step Execution: {step_name}\nStatus: {status_str}\nDuration: {duration_ms}ms"
                if hasattr(step, 'exception') and step.exception:
                    execution_log += f"\nException: {step.exception}"
                self.reporter_manager.get_rp_client().log_message(execution_log, "INFO")
            self._call_rp_client(_log_execution_details)

            # Log step-level data (network, console activity)
            try:
                self._log_step_data(step_name)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as log_error:
                self.logger.warning(f"Failed to log step data: {log_error}")

            # Attach step-level data (network logs, console logs, performance metrics)
            self.logger.info(f"[ATTACH DEBUG] Attaching data for step: {step_name}")
            try:
                self._attach_step_data(step_name)
                self.logger.info(f"[ATTACH DEBUG] Step data attached successfully")
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as attach_error:
                self.logger.warning(f"Failed to attach step data: {attach_error}")

            # Finish step in ReportPortal
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().finish_step(status_str)
            )

    def _log_step_data(self, step_name: str) -> None:
        """
        Log step-level data for visibility in ReportPortal logs.

        Args:
            step_name: Name of the step
        """
        rp_client = self.reporter_manager.get_rp_client()
        if not rp_client:
            return

        # Log network activity using specialized reporter
        try:
            self.network_reporter.log_network_activity(rp_client, step_name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(f"Failed to log network activity: {e}")

        # Log console activity using specialized reporter
        try:
            self.console_reporter.log_console_activity(rp_client, step_name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(f"Failed to log console activity: {e}")

    def _attach_step_data(self, step_name: str) -> None:
        """
        Add step-level data as attachments within the step.

        Args:
            step_name: Name of the step
        """
        rp_client = self.reporter_manager.get_rp_client()
        if not rp_client:
            return

        # Attach network logs
        try:
            self.network_reporter.attach_network_logs(rp_client, step_name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(f"Failed to attach network logs: {e}")

        # Attach console logs
        try:
            self.console_reporter.attach_console_logs(rp_client, step_name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(f"Failed to attach console logs: {e}")

        # Attach performance metrics
        try:
            self.performance_reporter.attach_performance_metrics(rp_client, step_name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(f"Failed to attach performance metrics: {e}")

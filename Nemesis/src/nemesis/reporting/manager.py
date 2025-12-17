"""Central reporting manager with config-driven architecture."""
import os
import traceback
from pathlib import Path
from typing import Any, Optional

from nemesis.infrastructure.config import ConfigLoader
from nemesis.shared.execution_context import ExecutionContext
from nemesis.infrastructure.logging import Logger
from nemesis.reporting.management.execution_manager import ExecutionManager
from nemesis.reporting.management.reporter_manager import ReporterManager
from nemesis.reporting.management.feature_manager import FeatureManager
from nemesis.reporting.management.scenario_manager import ScenarioManager
from nemesis.reporting.management.step_manager import StepManager
from nemesis.reporting.management.attachment_manager import AttachmentManager
from nemesis.reporting.management.finalization_manager import FinalizationManager
from nemesis.utils.helpers.scenario_helpers import normalize_scenario_status


class ReportManager:
    """Manages all reporting activities with config-driven architecture."""

    def __init__(self, context: Optional[Any] = None, skip_rp_init: bool = False) -> None:
        """Initialize report manager.

        Args:
            context: Behave context (optional)
            skip_rp_init: If True, skip ReportPortal initialization (for finalization phase)
        """
        self.context = context
        self.logger = Logger.get_instance({})
        self.skip_rp_init = skip_rp_init

        # Load centralized configuration
        self.config = ConfigLoader()

        # Get reporting settings from config
        self.local_enabled = self.config.get("reporting.local.enabled", True)
        self.rp_enabled = self.config.get("reporting.reportportal.enabled", False)

        # Initialize execution manager ONLY if local is enabled
        if self.local_enabled:
            # Check if we have an execution ID from environment (from CLI finalization)
            if 'NEMESIS_EXECUTION_ID' in os.environ:
                current_execution_id = os.environ['NEMESIS_EXECUTION_ID']
                self.logger.info(f"Using execution ID from environment: {current_execution_id}")
                ExecutionContext.set_execution_id(current_execution_id)

            self.execution_manager = ExecutionManager(self.config)
            self._propagate_execution_id()
        else:
            # Minimal execution manager for non-local reporting
            self.execution_manager = None

        # Initialize reporter manager
        # Pass skip_rp_init flag to prevent duplicate launches in finalization
        self.reporter_manager = ReporterManager(self.config, self.execution_manager, skip_rp_init=skip_rp_init)

        # Initialize management components
        self.feature_manager = FeatureManager(self.reporter_manager)
        self.scenario_manager = ScenarioManager(self.reporter_manager)
        self.step_manager = StepManager(self.reporter_manager)

        if self.execution_manager:
            self.attachment_manager = AttachmentManager(self.reporter_manager, self.execution_manager)
            self.finalization_manager = FinalizationManager(self.reporter_manager, self.execution_manager)
        else:
            self.attachment_manager = None
            self.finalization_manager = None

    def _propagate_execution_id(self) -> None:
        """Propagate execution_id to logging system."""
        if not self.execution_manager:
            return

        try:
            from nemesis.infrastructure.logging import get_factory  # pylint: disable=import-outside-toplevel
            factory = get_factory()
            context_manager = factory.get_context_manager()
            execution_id = self.execution_manager.get_execution_id()
            correlation_id = context_manager.start_correlation(execution_id=execution_id)
            self.logger.info(f"Execution ID propagated: {execution_id}, Correlation ID: {correlation_id}")

            os.environ['NEMESIS_EXECUTION_ID'] = execution_id
        except (AttributeError, KeyError, RuntimeError) as e:
            # Execution context propagation errors
            self.logger.warning(f"Failed to propagate execution_id: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportManager", method="__init__")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from execution context operations
            # NOTE: ExecutionContext or os.environ may raise various exceptions we cannot predict
            self.logger.warning(f"Failed to propagate execution_id: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportManager", method="__init__")

    def start_test_suite(self) -> None:
        """Start test suite reporting."""
        if self.execution_manager:
            self.execution_manager.start_execution()
        self.logger.info("Test suite started")

    def start_feature(self, feature: Any) -> None:
        """Start feature reporting."""
        self.feature_manager.start_feature(feature)

    def end_feature(self, feature: Any, status: str = None) -> None:
        """End feature reporting.

        Args:
            feature: Feature object
            status: Status string ("passed" or "failed") - if None, will be extracted from feature
        """
        self.feature_manager.end_feature(feature, status)

    def start_scenario(self, scenario: Any) -> None:
        """Start scenario reporting."""
        # Direct call to local reporter for immediate data collection
        if self.local_enabled and self.reporter_manager.get_local_reporter():
            Logger.get_instance({}).info(f"[DEBUG] ReportManager: LocalReporter available, starting scenario: {scenario.name}")
            self.reporter_manager.get_local_reporter().start_scenario(scenario)
            self.logger.debug(f"LocalReporter started scenario: {scenario.name}")
        else:
            Logger.get_instance({}).info(f"[DEBUG] ReportManager: LocalReporter not available for scenario: {scenario.name}")
            self.logger.warning(f"LocalReporter not available for scenario: {scenario.name}")

        self.scenario_manager.start_scenario(scenario)

    def end_scenario(self, scenario: Any, status: str = None) -> None:
        """End scenario reporting.

        Args:
            scenario: Scenario object
            status: Status string ("passed" or "failed") - if None, will be extracted from scenario
        """
        # Extract status from scenario if not provided
        status_str = normalize_scenario_status(scenario, status)

        # Direct call to local reporter for immediate data collection
        if self.local_enabled and self.reporter_manager.get_local_reporter():
            self.reporter_manager.get_local_reporter().end_scenario(scenario, status_str)

        self.scenario_manager.end_scenario(scenario, status_str)

    def start_step(self, step: Any) -> None:
        """Start step reporting."""
        # Direct call to local reporter for immediate data collection
        if self.local_enabled and self.reporter_manager.get_local_reporter():
            self.reporter_manager.get_local_reporter().start_step(step)

        self.step_manager.start_step(step)

    def end_step(self, step: Any, duration: float = 0.0) -> None:
        """End step reporting."""
        # Direct call to local reporter for immediate data collection
        if self.local_enabled and self.reporter_manager.get_local_reporter():
            status = getattr(step, 'status', 'passed')
            self.reporter_manager.get_local_reporter().end_step(step, status)

        self.step_manager.end_step(step, duration)

    def attach_screenshot(self, screenshot: bytes, name: str) -> None:
        """Attach screenshot to reports."""
        if self.attachment_manager:
            self.attachment_manager.attach_screenshot(screenshot, name)

    def attach_video(self, video_path) -> None:
        """Attach a video (local storage + optional ReportPortal upload)."""
        if self.attachment_manager:
            self.attachment_manager.attach_video(video_path)

    def attach_trace(self, trace_path) -> None:
        """Attach a Playwright trace (local storage + optional ReportPortal upload)."""
        if self.attachment_manager:
            self.attachment_manager.attach_trace(trace_path)

    def attach_metrics(self, metrics_path, metric_type: str) -> None:
        """Attach metrics file (local storage + optional ReportPortal upload)."""
        if self.attachment_manager:
            self.attachment_manager.attach_metrics(metrics_path, metric_type)

    def attach_file(self, file_path, description: str = "", attachment_type: str = "") -> None:
        """Attach file to reports with optional attachment_type for filtering.

        Args:
            file_path: Path to file to attach
            description: Description of the attachment
            attachment_type: Type of attachment (e.g., 'har', 'console', 'metrics', 'screenshot', 'video', 'trace')
        """
        if self.attachment_manager:
            self.attachment_manager.attach_file(file_path, description, attachment_type)

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message to reports."""
        if self.attachment_manager:
            self.attachment_manager.log_message(message, level)

    def finalize(self) -> None:
        """Finalize all reporting.

        This method finalizes both local and ReportPortal reports.
        Should be called in after_all hook to ensure context and launch_id are available.
        """
        if self.finalization_manager:
            # Finalize both local (HTML) and ReportPortal reports
            self.finalization_manager.finalize()
        else:
            self.logger.warning("Finalization manager not available")

    def cleanup(self) -> None:
        """Cleanup reporting resources."""
        try:
            if self.execution_manager:
                self.execution_manager.cleanup()
            self.logger.info("ReportManager cleanup completed")
        except (AttributeError, RuntimeError) as e:
            # Cleanup operation errors
            self.logger.error(f"ReportManager cleanup failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportManager", method="cleanup")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from cleanup operations
            # NOTE: ExecutionManager cleanup may raise various exceptions we cannot predict
            self.logger.error(f"ReportManager cleanup failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportManager", method="cleanup")

    def get_execution_path(self) -> Optional[Path]:
        """Get execution directory path."""
        if self.execution_manager:
            return self.execution_manager.get_execution_path()
        return None

    def get_execution_id(self) -> str:
        """Get execution ID."""
        if self.execution_manager:
            return self.execution_manager.get_execution_id()
        return "no-execution-id"

    def is_healthy(self) -> bool:
        """Check if at least one reporter is active."""
        if self.finalization_manager:
            return self.finalization_manager.is_healthy()
        return False

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        """Cleanup on context exit."""
        try:
            self.finalize()
        except (AttributeError, RuntimeError) as e:
            # Report finalization errors
            self.logger.error(f"Error during report finalization: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportManager", method="__exit__")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from finalization
            # NOTE: FinalizationManager may raise various exceptions we cannot predict
            self.logger.error(f"Error during report finalization: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ReportManager", method="__exit__")
        return False

    def __repr__(self) -> str:
        return (
            f"ReportManager(execution_id={self.get_execution_id()}, "
            f"local={self.local_enabled}, rp={self.rp_enabled})"
        )

    # Backward compatibility properties
    @property
    def local_reporter(self):
        """Backward compatibility for local_reporter."""
        return self.reporter_manager.get_local_reporter()

    @property
    def rp_client(self):
        """Backward compatibility for rp_client."""
        return self.reporter_manager.get_rp_client()

    @property
    def execution_id(self) -> str:
        """Backward compatibility for execution_id."""
        return self.get_execution_id()

    @property
    def execution_path(self) -> Optional[Path]:
        """Backward compatibility for execution_path."""
        return self.get_execution_path()

    def end_test_suite(self, status: Optional[str] = None) -> None:
        """End test suite reporting.

        Args:
            status: Optional test suite status (for logging purposes)
        """
        if self.execution_manager:
            self.execution_manager.end_execution()
        status_msg = f" (status: {status})" if status else ""
        self.logger.info(f"Test suite reporting ended{status_msg}")

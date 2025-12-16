"""Step management for reporting."""
import traceback

from nemesis.core.logging import Logger


class StepManager:
    """Manages step reporting."""

    def __init__(self, reporter_manager):
        """Initialize step manager."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

    def start_step(self, step) -> None:
        """Start step reporting."""
        step_name = getattr(step, 'name', str(step))

        self.logger.step_start(step_name)

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().start_step(step_name)
            except (AttributeError, RuntimeError) as e:
                # ReportPortal client errors - non-critical, log as debug
                self.logger.debug(f"Failed to start step in ReportPortal: {e}", module=__name__, class_name="StepManager", method="start_step")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to start step in ReportPortal: {e}", module=__name__, class_name="StepManager", method="start_step")

        if self.reporter_manager.is_local_enabled():
            try:
                self.reporter_manager.get_local_reporter().start_step(step)
                self.reporter_manager.get_local_reporter().add_log(f"Step started: {step_name}", "INFO")
            except (AttributeError, RuntimeError) as e:
                # Local reporter errors - non-critical, log as debug
                self.logger.debug(f"Failed to start step in local reporter: {e}", module=__name__, class_name="StepManager", method="start_step")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: Local reporter may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to start step in local reporter: {e}", module=__name__, class_name="StepManager", method="start_step")

    def end_step(self, step, duration: float = 0.0) -> None:
        """End step reporting."""
        step_name = getattr(step, 'name', str(step))
        status = getattr(step, 'status', None)

        if hasattr(status, 'name'):
            status_str = "PASSED" if status.name == "passed" else "FAILED"
        else:
            status_str = "PASSED"

        # Convert duration to milliseconds
        # Handle case where duration might be string or other type
        try:
            duration_float = float(duration) if duration else 0.0
            duration_ms = int(duration_float * 1000) if duration_float > 0 else 0
        except (ValueError, TypeError):
            duration_ms = 0
        self.logger.step_end(step_name, status_str, duration_ms)

        if self.reporter_manager.is_local_enabled():
            try:
                self.reporter_manager.get_local_reporter().end_step(step, status_str)
                self.reporter_manager.get_local_reporter().add_log(f"Step ended: {step_name} - Status: {status_str} - Duration: {duration_ms}ms", "INFO")
            except (AttributeError, RuntimeError) as e:
                # Local reporter errors - non-critical, log as debug
                self.logger.debug(f"Failed to add step to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="StepManager", method="end_step")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: Local reporter may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to add step to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="StepManager", method="end_step")

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().finish_step(status_str)
            except (AttributeError, RuntimeError) as e:
                # ReportPortal client errors - non-critical, log as debug
                self.logger.debug(f"Failed to finish step in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="StepManager", method="end_step")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to finish step in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="StepManager", method="end_step")

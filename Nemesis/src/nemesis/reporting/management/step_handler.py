"""Step management for reporting."""
from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class StepHandler:
    """Handles step reporting."""

    def __init__(self, reporter_manager):
        """Initialize step handler."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to call local reporter: {error}",
        fallback_message="Failed to call local reporter: {error}"
    )
    def _call_local_reporter(self, callback) -> None:
        """Call local reporter method with exception handling."""
        callback()

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to call ReportPortal: {error}",
        fallback_message="Failed to call ReportPortal: {error}"
    )
    def _call_rp_client(self, callback) -> None:
        """Call ReportPortal client method with exception handling."""
        callback()

    def start_step(self, step) -> None:
        """Start step reporting."""
        step_name = getattr(step, 'name', str(step))

        self.logger.step_start(step_name)

        if self.reporter_manager.is_rp_enabled():
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().start_step(step_name)
            )

        if self.reporter_manager.is_local_enabled():
            def _start_local():
                self.reporter_manager.get_local_reporter().start_step(step)
                self.reporter_manager.get_local_reporter().add_log(f"Step started: {step_name}", "INFO")
            self._call_local_reporter(_start_local)

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
            def _end_local():
                self.reporter_manager.get_local_reporter().end_step(step, status_str)
                self.reporter_manager.get_local_reporter().add_log(f"Step ended: {step_name} - Status: {status_str} - Duration: {duration_ms}ms", "INFO")
            self._call_local_reporter(_end_local)

        if self.reporter_manager.is_rp_enabled():
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().finish_step(status_str)
            )

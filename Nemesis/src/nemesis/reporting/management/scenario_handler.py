"""Scenario management for reporting."""
from nemesis.infrastructure.logging import Logger
from nemesis.utils.helpers.scenario_helpers import normalize_scenario_status_for_rp
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class ScenarioHandler:
    """Handles scenario reporting."""

    def __init__(self, reporter_manager):
        """Initialize scenario handler."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to call local reporter: {error}",
        fallback_message="Failed to call local reporter: {error}"
    )
    def _call_local_reporter(self, callback) -> None:
        """Call local reporter method with exception handling."""
        callback()

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="{error}",
        fallback_message="{error}"
    )
    def _call_rp_client(self, callback) -> None:
        """Call ReportPortal client method with exception handling."""
        callback()

    def start_scenario(self, scenario) -> None:
        """Start scenario reporting with support for advanced tags."""
        scenario_name = getattr(scenario, 'name', str(scenario))
        tags = getattr(scenario, 'tags', [])
        description = getattr(scenario, 'description', '')

        self.logger.scenario_start(scenario_name)

        if self.reporter_manager.is_local_enabled():
            def _start_local():
                self.reporter_manager.get_local_reporter().start_scenario(scenario)
                self.reporter_manager.get_local_reporter().add_log(f"Scenario started: {scenario_name}", "INFO")
            self._call_local_reporter(_start_local)

        if self.reporter_manager.is_rp_enabled():
            desc_text = '\n'.join(description) if isinstance(description, list) else description
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().start_test(scenario_name, "SCENARIO", tags, desc_text)
            )

    def end_scenario(self, scenario, status: str = None) -> None:
        """End scenario reporting.

        Args:
            scenario: Scenario object
            status: Status string ("passed" or "failed") - if None, will be extracted from scenario
        """
        scenario_name = getattr(scenario, 'name', str(scenario))

        # Use provided status or extract from scenario
        status_str = normalize_scenario_status_for_rp(scenario, status)

        # Calculate duration - use scenario duration if available, otherwise 0
        duration_ms = getattr(scenario, 'duration_ms', 0)
        if duration_ms == 0:
            # Try to calculate from start/end times if available
            start_time = getattr(scenario, 'start_time', None)
            end_time = getattr(scenario, 'end_time', None)
            if start_time and end_time:
                duration_ms = int((end_time - start_time) * 1000)

        self.logger.scenario_end(scenario_name, status_str, duration_ms)

        if self.reporter_manager.is_local_enabled():
            def _end_local():
                self.reporter_manager.get_local_reporter().end_scenario(scenario, status_str)
                self.reporter_manager.get_local_reporter().add_log(f"Scenario ended: {scenario_name} - Status: {status_str} - Duration: {duration_ms}ms", "INFO")
            self._call_local_reporter(_end_local)

        # IMPORTANT: Finish test in ReportPortal AFTER attachments are added
        # test_id is kept even after finish_test() to allow attachments after finish
        if self.reporter_manager.is_rp_enabled():
            def _finish_rp():
                self.reporter_manager.get_rp_client().finish_test(status_str)
                self.logger.debug(f"Scenario finished in ReportPortal: {scenario_name} - {status_str}")
            self._call_rp_client(_finish_rp)

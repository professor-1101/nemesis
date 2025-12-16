"""Scenario management for reporting."""
import traceback

from nemesis.core.logging import Logger
from nemesis.utils.helpers.scenario_helpers import normalize_scenario_status_for_rp


class ScenarioManager:
    """Manages scenario reporting."""

    def __init__(self, reporter_manager):
        """Initialize scenario manager."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

    def start_scenario(self, scenario) -> None:
        """Start scenario reporting."""
        scenario_name = getattr(scenario, 'name', str(scenario))

        self.logger.scenario_start(scenario_name)

        if self.reporter_manager.is_local_enabled():
            try:
                self.reporter_manager.get_local_reporter().start_scenario(scenario)
                self.reporter_manager.get_local_reporter().add_log(f"Scenario started: {scenario_name}", "INFO")
            except (AttributeError, RuntimeError) as e:
                # Local reporter errors
                self.logger.error(f"Failed to start scenario in local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="start_scenario")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: Local reporter may raise various exceptions we cannot predict
                self.logger.error(f"Failed to start scenario in local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="start_scenario")

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().start_test(scenario_name, "SCENARIO")
            except (AttributeError, RuntimeError) as e:
                # ReportPortal client errors
                self.logger.error(f"Failed to start scenario in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="start_scenario")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Failed to start scenario in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="start_scenario")

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
            try:
                self.reporter_manager.get_local_reporter().end_scenario(scenario, status_str)
                self.reporter_manager.get_local_reporter().add_log(f"Scenario ended: {scenario_name} - Status: {status_str} - Duration: {duration_ms}ms", "INFO")
            except (AttributeError, RuntimeError) as e:
                # Local reporter errors
                self.logger.error(f"Failed to finish scenario in local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="end_scenario")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: Local reporter may raise various exceptions we cannot predict
                self.logger.error(f"Failed to finish scenario in local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="end_scenario")

        # IMPORTANT: Finish test in ReportPortal AFTER attachments are added
        # test_id is kept even after finish_test() to allow attachments after finish
        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().finish_test(status_str)
                self.logger.debug(f"Scenario finished in ReportPortal: {scenario_name} - {status_str}")
            except (AttributeError, RuntimeError) as e:
                # ReportPortal client errors
                self.logger.error(f"Failed to finish scenario in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="end_scenario")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Failed to finish scenario in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="ScenarioManager", method="end_scenario")

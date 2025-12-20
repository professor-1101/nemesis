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

        # Extract feature name and code reference for attributes
        feature_name = ""
        code_ref = ""
        if hasattr(scenario, 'feature') and scenario.feature:
            feature_name = getattr(scenario.feature, 'name', '')
            # Extract code reference (feature file path)
            if hasattr(scenario.feature, 'filename'):
                code_ref = getattr(scenario.feature, 'filename', '')

        self.logger.scenario_start(scenario_name)

        # Update environment context for attachment naming
        from nemesis.infrastructure.environment.hooks import _get_env_manager
        env_manager = _get_env_manager()
        if env_manager:
            env_manager.set_current_scenario(scenario_name)

        if self.reporter_manager.is_local_enabled():
            def _start_local():
                self.reporter_manager.get_local_reporter().start_scenario(scenario)
                self.reporter_manager.get_local_reporter().add_log(f"Scenario started: {scenario_name}", "INFO")
            self._call_local_reporter(_start_local)

        if self.reporter_manager.is_rp_enabled():
            # Add feature_name and code_ref to tags for attributes
            enhanced_tags = tags.copy() if tags else []
            if feature_name:
                enhanced_tags.append(f"@feature:{feature_name}")
            if code_ref:
                enhanced_tags.append(f"@code_ref:{code_ref}")

            # Performance attributes are logged as messages in end_scenario, not added as tags
            # because attributes must be set during test start, not after

            desc_text = '\n'.join(description) if isinstance(description, list) else description

            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().start_test(scenario_name, "TEST", enhanced_tags, desc_text)
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
            # Log scenario stack trace (execution history)
            self._log_scenario_stack_trace()

            # Performance metrics are logged as INFO messages above

            # Log performance data before finishing test
            perf_summary = self._get_performance_summary()
            if perf_summary:
                def _log_performance():
                    self.reporter_manager.get_rp_client().log_message(
                        f"Performance Metrics:\n\n{perf_summary}",
                        "INFO"
                    )
                self._call_rp_client(_log_performance)

            def _finish_rp():
                self.reporter_manager.get_rp_client().finish_test(status_str)
                self.logger.debug(f"Scenario finished in ReportPortal: {scenario_name} - {status_str}")
            self._call_rp_client(_finish_rp)

    def _log_scenario_stack_trace(self) -> None:
        """Log scenario execution history as stack trace."""
        try:
            # Get environment manager to access scenario actions
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()

            if env_manager:
                actions = env_manager.get_scenario_actions()
                if actions:
                    # Create a custom exception for stack trace display
                    class ScenarioExecutionHistory(Exception):
                        def __init__(self, actions):
                            self.actions = actions
                            super().__init__("Complete Scenario Execution History")

                        def __str__(self):
                            actions_list = []
                            for i, action in enumerate(self.actions, 1):
                                actions_list.append(f"{i:2d}. {action}")
                            return f"Complete Scenario Execution History:\n" + "\n".join(actions_list)

                    execution_history = ScenarioExecutionHistory(actions)

                    def _log_scenario_stack_trace():
                        self.reporter_manager.get_rp_client().log_message(
                            str(execution_history),
                            "INFO"
                        )
                    self._call_rp_client(_log_scenario_stack_trace)
                    self.logger.info(f"Logged scenario execution history with {len(actions)} actions")

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to log scenario stack trace: {e}")

    def _add_performance_attributes(self) -> None:
        """Performance attributes are now logged as messages in end_scenario."""
        # Performance metrics are logged as INFO messages in end_scenario
        # Attributes cannot be added after test start in ReportPortal
        pass

    def _get_performance_summary(self) -> str:
        """Get performance metrics summary for scenario description."""
        try:
            # Get performance collector data
            from nemesis.infrastructure.collectors import get_collector
            perf_collector = get_collector('performance')
            if perf_collector:
                perf_data = perf_collector.get_data()
                if perf_data:
                    lines = []

                    # Key metrics in compact format
                    if 'navigation' in perf_data:
                        nav = perf_data['navigation']
                        lines.append(f"Load Time: {nav.get('total_load', 0):.0f}ms | DNS: {nav.get('dns_lookup', 0):.0f}ms | TCP: {nav.get('tcp_connection', 0):.0f}ms | TTFB: {nav.get('ttfb', 0):.0f}ms")

                    if 'web_vitals' in perf_data:
                        vitals = perf_data['web_vitals']
                        lines.append(f"FCP: {vitals.get('fcp', 0):.0f}ms | LCP: {vitals.get('lcp', 0):.0f}ms | CLS: {vitals.get('cls', 0):.3f} | TTI: {vitals.get('tti', 0):.0f}ms")

                    if 'memory' in perf_data:
                        mem = perf_data['memory']
                        lines.append(f"Memory: {mem.get('used_js_heap', 0)/1024/1024:.1f}MB used ({mem.get('heap_usage', 0):.1f}%)")

                    if 'resources' in perf_data:
                        res = perf_data['resources']
                        lines.append(f"Resources: {res.get('total_count', 0)} files | {res.get('total_transfer', 0)/1024:.1f}KB transferred")

                    # Performance metrics are logged as formatted messages below
                    # No need to store as attributes since they can't be added after test start

                    return "\n".join(lines)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to get performance summary: {e}")

        return ""

"""Step management for reporting."""
from datetime import datetime
from typing import Any, Callable

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class StepHandler:
    """Handles step reporting."""

    def __init__(self, reporter_manager: Any) -> None:
        """Initialize step handler."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

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
        """Start step reporting."""
        step_name = getattr(step, 'name', str(step))

        # Replace PLACEHOLDER values with actual data for better reporting
        # Get actual data from context if available
        try:
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()
            if env_manager and hasattr(env_manager, 'context'):
                context = env_manager.context
                if hasattr(context, 'current_user_data') and context.current_user_data:
                    user_data = context.current_user_data
                    username = user_data.get('نام_کاربری', '')
                    password = user_data.get('رمز_عبور', '')
                    if username:
                        step_name = step_name.replace('"PLACEHOLDER"', f'"{username}"')
                    if password and '"رمز_عبور"' in step_name:
                        step_name = step_name.replace('"PLACEHOLDER"', f'"{password}"')
        except Exception:
            pass  # Fallback to original step name

        # Extract feature and scenario names for attributes
        feature_name = ""
        scenario_name = ""
        code_ref = ""

        if hasattr(step, 'scenario') and step.scenario:
            scenario_name = getattr(step.scenario, 'name', '')
            if hasattr(step.scenario, 'feature') and step.scenario.feature:
                feature_name = getattr(step.scenario.feature, 'name', '')
                # Extract code reference from feature
                if hasattr(step.scenario.feature, 'filename'):
                    code_ref = getattr(step.scenario.feature, 'filename', '')

        self.logger.step_start(step_name)

        # Update environment context for attachment naming
        from nemesis.infrastructure.environment.hooks import _get_env_manager
        env_manager = _get_env_manager()
        if env_manager:
            env_manager.set_current_step(step_name)

        if self.reporter_manager.is_rp_enabled():
            # Create tags with feature, scenario, and code_ref info for attributes
            tags = []
            if feature_name:
                tags.append(f"@feature:{feature_name}")
            if scenario_name:
                tags.append(f"@scenario:{scenario_name}")
            if 'code_ref' in locals() and code_ref:
                tags.append(f"@code_ref:{code_ref}")

            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().start_step(step_name, tags)
            )

        if self.reporter_manager.is_local_enabled():
            def _start_local():
                self.reporter_manager.get_local_reporter().start_step(step)
                self.reporter_manager.get_local_reporter().add_log(f"Step started: {step_name}", "INFO")
            self._call_local_reporter(_start_local)

    def end_step(self, step: Any, duration: float = 0.0) -> None:
        """End step reporting."""
        step_name = getattr(step, 'name', str(step))
        status = getattr(step, 'status', None)

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
            # Skip step-level stack trace to avoid duplication - only show at scenario level

            # Log execution details before finishing step
            def _log_execution_details():
                execution_log = f"Step Execution: {step_name}\nStatus: {status_str}\nDuration: {duration_ms}ms"
                if hasattr(step, 'exception') and step.exception:
                    execution_log += f"\nException: {step.exception}"
                self.reporter_manager.get_rp_client().log_message(execution_log, "INFO")
            self._call_rp_client(_log_execution_details)

            # Log step-level data for visibility in logs
            try:
                self._log_step_data(step, step_name, status_str)
            except Exception as log_error:  # pylint: disable=broad-exception-caught
                self.logger.warning(f"Failed to log step data: {log_error}")

            # Attach step-level data before finishing step
            self.logger.info(f"[ATTACH DEBUG] Attaching data for step: {step_name}")
            try:
                self._attach_step_data(step, step_name, status_str)
                self.logger.info(f"[ATTACH DEBUG] Step data attached successfully")
            except Exception as attach_error:  # pylint: disable=broad-exception-caught
                self.logger.warning(f"Failed to attach step data: {attach_error}")

            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().finish_step(status_str)
            )

    def _log_step_stack_trace(self, step_name: str) -> None:
        """Log step execution history as readable log message."""
        try:
            # Get environment manager to access step actions
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()

            if env_manager:
                actions = env_manager.get_step_actions()
                if actions:
                    # Create a custom exception for step stack trace display
                    class StepExecutionHistory(Exception):
                        def __init__(self, actions, step_name):
                            self.step_name = step_name
                            self.actions = actions
                            super().__init__(f"Step Actions - {step_name}")

                        def __str__(self):
                            actions_list = []
                            for i, action in enumerate(self.actions, 1):
                                actions_list.append(f"{i:2d}. {action}")
                            return f"Step Actions - {self.step_name}:\n" + "\n".join(actions_list)

                    execution_history = StepExecutionHistory(actions, step_name)

                    def _log_step_stack_trace():
                        self.reporter_manager.get_rp_client().log_message(
                            str(execution_history),
                            "INFO"
                        )
                    self._call_rp_client(_log_step_stack_trace)
                    self.logger.info(f"Logged step actions for '{step_name}' with {len(actions)} actions")

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to log step actions: {e}")

    def _log_step_data(self, step: Any, step_name: str, status: str) -> None:
        """Log step-level data for visibility in ReportPortal logs."""
        rp_client = self.reporter_manager.get_rp_client()
        if not rp_client:
            return

        # Log network activity
        try:
            self._log_network_activity(rp_client, step_name)
        except Exception as log_error:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to log network activity: {log_error}")

        # Log console activity
        try:
            self._log_console_activity(rp_client, step_name)
        except Exception as log_error:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to log console activity: {log_error}")

    def _attach_step_data(self, step: Any, step_name: str, status: str) -> None:
        """Add step-level data as attachments within the step."""
        rp_client = self.reporter_manager.get_rp_client()
        if not rp_client:
            return

        # Get current context for naming
        from nemesis.infrastructure.environment.hooks import _get_env_manager
        env_manager = _get_env_manager()
        context = env_manager.get_attachment_context() if env_manager else {}

        feature_name = context.get('feature', 'unknown_feature')
        scenario_name = context.get('scenario', 'unknown_scenario')

        # Performance metrics are handled at scenario level, not step level

        # 2. Attach network logs as file attachment
        try:
            self._attach_network_logs(rp_client, step_name, feature_name, scenario_name)
        except Exception as attach_error:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach network logs: {attach_error}")

        # 3. Attach console logs as file attachment
        try:
            self._attach_console_logs(rp_client, step_name, feature_name, scenario_name)
        except Exception as attach_error:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach console logs: {attach_error}")

        # 4. Attach performance metrics as file attachment
        try:
            self._attach_performance_metrics(rp_client, step_name, feature_name, scenario_name)
        except Exception as attach_error:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach performance metrics: {attach_error}")

        # 5. Add screenshot as attachment (required for each step)
        try:
            screenshot_path = self._capture_and_attach_screenshot(rp_client, step_name, feature_name, scenario_name)
            if screenshot_path:
                self.logger.debug(f"Screenshot attached: {screenshot_path}")
        except Exception as attach_error:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach screenshot: {attach_error}")

    def _capture_and_attach_screenshot(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> str:
        """Capture and attach screenshot for the step."""
        try:
            # Try to get browser adapter from the environment manager context
            # The environment manager is stored in the step's context
            try:
                # Get environment manager
                from nemesis.infrastructure.environment.hooks import _get_env_manager
                env_manager = _get_env_manager()

                if env_manager and hasattr(env_manager, 'browser_env') and env_manager.browser_env:
                    browser_env = env_manager.browser_env
                    if hasattr(browser_env, '_current_page_adapter') and browser_env._current_page_adapter:
                        page_adapter = browser_env._current_page_adapter

                        # Capture real screenshot
                        self.logger.info(f"[SCREENSHOT DEBUG] Capturing real screenshot for step: {step_name}")
                        screenshot_bytes = page_adapter.screenshot()

                        # Generate unique name
                        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                        sanitized_step = self._sanitize_filename(step_name)
                        name = f"{feature_name}__{scenario_name}__{sanitized_step}__screenshot__{timestamp}.png"

                        # Attach to ReportPortal
                        self.logger.info(f"[SCREENSHOT DEBUG] Attaching real screenshot to RP: {name}")
                        rp_client.attach_file(screenshot_bytes, f"Screenshot: {step_name}", "screenshot")
                        self.logger.info(f"[SCREENSHOT DEBUG] Real screenshot attached successfully")
                        return f"Screenshot attached: {name}"
                    else:
                        self.logger.warning("[SCREENSHOT DEBUG] Page adapter not available")
                else:
                    self.logger.warning("[SCREENSHOT DEBUG] Environment manager not available")

                # Fallback to dummy screenshot if we can't access the real browser
                self.logger.info(f"[SCREENSHOT DEBUG] Browser access failed - creating dummy attachment")

            except Exception as page_error:
                self.logger.warning(f"[SCREENSHOT DEBUG] Cannot access browser page: {page_error}")

            # Create a dummy PNG image (1x1 transparent pixel)
            dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'

            # Generate unique name
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            sanitized_step = self._sanitize_filename(step_name)
            name = f"{feature_name}__{scenario_name}__{sanitized_step}__screenshot__{timestamp}"

            # Attach to ReportPortal
            self.logger.info(f"[SCREENSHOT DEBUG] Attaching dummy screenshot to RP: {name}")
            rp_client.attach_file(dummy_png, f"Screenshot: {step_name}", "screenshot")
            self.logger.info(f"[SCREENSHOT DEBUG] Dummy screenshot attached successfully")
            return f"Screenshot attached: {name}"

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to capture screenshot: {e}")
        return ""

    def _log_network_activity(self, rp_client, step_name: str) -> None:
        """Log network activity as step-level log in ReportPortal."""
        try:
            # Get network collector data
            network_collector = self._get_collector_data('network')
            if network_collector:
                # Format network data
                network_summary = self._format_network_data(network_collector)
                if network_summary:
                    # Check if there are network errors (4xx, 5xx status codes)
                    has_errors = any(req.get('status', 0) >= 400 for req in network_collector
                                   if isinstance(req, dict)) if network_collector else False

                    # Log network summary as step-level log
                    if has_errors:
                        # Use exception (stack trace) for errors
                        class NetworkErrorException(Exception):
                            def __init__(self, summary):
                                self.summary = summary
                                super().__init__("Network Errors Detected")

                            def __str__(self):
                                return f"Network Errors:\n\n{self.summary}"

                        network_exception = NetworkErrorException(network_summary)
                        rp_client.log_exception(network_exception, f"Network activity for step: {step_name}")
                    else:
                        # Use regular message for successful requests
                        rp_client.log_message(f"Network Activity ({len(network_collector)} requests):\n\n{network_summary}",
                                            "INFO")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to log network activity: {e}")

    def _attach_network_logs(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """Attach network logs as file attachment."""
        try:
            # Get network collector data
            network_collector = self._get_collector_data('network')
            if network_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                sanitized_step = self._sanitize_filename(step_name)
                name = f"network_logs_{timestamp}"

                # Convert to JSON and attach
                import json
                network_json = json.dumps(network_collector, indent=2)
                rp_client.attach_file(network_json.encode('utf-8'), name, "network_logs")
                self.logger.debug(f"Network logs attached: {len(network_json)} bytes")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach network logs: {e}")

    def _attach_performance_metrics(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """Attach performance metrics collected during the step."""
        try:
            # Get performance collector data
            perf_collector = self._get_collector_data('performance')
            if perf_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                sanitized_step = self._sanitize_filename(step_name)
                name = f"{feature_name}__{scenario_name}__{sanitized_step}__performance__{timestamp}"

                # Convert to JSON and attach
                import json
                perf_json = json.dumps(perf_collector, indent=2)
                rp_client.attach_file(perf_json.encode('utf-8'), f"Performance Metrics: {step_name}", "performance_metrics")
                self.logger.debug(f"Performance metrics attached: {len(perf_json)} bytes")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach performance metrics: {e}")

    def _log_console_activity(self, rp_client, step_name: str) -> None:
        """Log console activity as step-level log in ReportPortal."""
        try:
            # Get console collector data
            console_collector = self._get_collector_data('console')
            if console_collector:
                # Format console data
                console_summary = self._format_console_data(console_collector)
                if console_summary:
                    # Check if there are errors in console output (only check actual log entries)
                    has_errors = False
                    if console_collector and isinstance(console_collector, list):
                        for log in console_collector:
                            if isinstance(log, dict):
                                log_type = log.get('type', '').lower()
                                if log_type == 'error':
                                    has_errors = True
                                    break

                    # Log console summary as step-level log
                    if has_errors:
                        # Use exception (stack trace) for console errors
                        class ConsoleErrorException(Exception):
                            def __init__(self, summary):
                                self.summary = summary
                                super().__init__("Console Errors Detected")

                            def __str__(self):
                                return f"Browser Console Errors:\n\n{self.summary}"

                        console_exception = ConsoleErrorException(console_summary)
                        rp_client.log_exception(console_exception, f"Browser console logs for step: {step_name}")
                    else:
                        # Use regular message for clean console
                        rp_client.log_message(f"Browser Console ({len(console_collector)} entries):\n\n{console_summary}",
                                            "INFO")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to log console activity: {e}")

    def _attach_console_logs(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """
        Attach console logs as file attachment.

        Enhanced formatting with emoji severity indicators and no truncation limits.
        """
        try:
            # Get console collector data
            console_collector = self._get_collector_data('console')
            if console_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                sanitized_step = self._sanitize_filename(step_name)
                name = f"console_logs_{timestamp}"

                # Use enhanced formatting method (shows all logs with emoji indicators)
                console_text = self._format_console_data(console_collector)

                rp_client.attach_file(console_text.encode('utf-8'), f"Console Logs: {step_name}", "console_logs")
                self.logger.debug(f"Console logs attached: {len(console_collector)} entries")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach console logs: {e}")

    def _add_performance_attributes(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """Performance attributes are handled at scenario level, not step level."""
        # Performance metrics are logged at scenario level as INFO messages
        # Step-level attributes are not supported by ReportPortal API
        pass

    def _attach_network_logs(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """Attach network logs collected during the step."""
        try:
            # Get network collector data
            network_collector = self._get_collector_data('network')
            if network_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                sanitized_step = self._sanitize_filename(step_name)
                name = f"{feature_name}__{scenario_name}__{sanitized_step}__network_logs__{timestamp}"

                # Convert to JSON and attach
                import json
                network_json = json.dumps(network_collector, indent=2)
                rp_client.attach_file(network_json.encode('utf-8'), f"Network Logs: {step_name}", "network_logs")
                self.logger.debug(f"Network logs attached: {len(network_json)} bytes")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach network logs: {e}")

    def _attach_console_logs(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """Attach console logs collected during the step."""
        try:
            # Get console collector data
            console_collector = self._get_collector_data('console')
            if console_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                sanitized_step = self._sanitize_filename(step_name)
                name = f"{feature_name}__{scenario_name}__{sanitized_step}__console_logs__{timestamp}"

                # Convert to text and attach
                console_text = "\n".join(str(log) for log in console_collector)
                rp_client.attach_file(console_text.encode('utf-8'), f"Console Logs: {step_name}", "console_logs")
                self.logger.debug(f"Console logs attached: {len(console_text)} lines")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach console logs: {e}")

    def _attach_performance_metrics(self, rp_client, step_name: str, feature_name: str, scenario_name: str) -> None:
        """Attach performance metrics collected during the step."""
        try:
            # Get performance collector data
            perf_collector = self._get_collector_data('performance')
            if perf_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                sanitized_step = self._sanitize_filename(step_name)
                name = f"{feature_name}__{scenario_name}__{sanitized_step}__performance__{timestamp}"

                # Convert to JSON and attach
                import json
                perf_json = json.dumps(perf_collector, indent=2)
                rp_client.attach_file(perf_json.encode('utf-8'), f"Performance Metrics: {step_name}", "performance_metrics")
                self.logger.debug(f"Performance metrics attached: {len(perf_json)} bytes")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to attach performance metrics: {e}")

    # _performance_data_to_attributes method removed - performance handled at scenario level

    def _format_network_data(self, network_data: Any) -> str:
        """
        Format network data as ASCII table with enhanced readability.

        Creates a structured table with:
        - Method | URL | Status | Duration | Size | Type
        - No truncation limits (shows all requests)
        - Grouped by request type (responses, requests, failed)
        """
        try:
            if isinstance(network_data, list):
                if not network_data:
                    return "No network activity captured."

                # Group by type
                responses = [r for r in network_data if r.get('type') == 'response']
                requests = [r for r in network_data if r.get('type') == 'request']
                failed = [r for r in network_data if r.get('type') == 'failed']

                sections = []

                # Summary header
                sections.append("=" * 120)
                sections.append(f"NETWORK ACTIVITY SUMMARY ({len(network_data)} total events)")
                sections.append("=" * 120)
                sections.append(f"✅ Responses: {len(responses)}")
                sections.append(f"📤 Requests: {len(requests)}")
                sections.append(f"❌ Failed: {len(failed)}")
                sections.append("=" * 120)
                sections.append("")

                # Responses table
                if responses:
                    sections.append(self._create_network_table("RESPONSES", responses, "✅"))
                    sections.append("")

                # Failed requests table
                if failed:
                    sections.append(self._create_network_failed_table("FAILED REQUESTS", failed, "❌"))
                    sections.append("")

                # Requests table (if only requests without responses)
                if requests:
                    sections.append(self._create_network_table("REQUESTS", requests, "📤"))
                    sections.append("")

                return "\n".join(sections).rstrip()
            return str(network_data)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to format network data: {e}")
            return ""

    def _create_network_table(self, section_name: str, entries: list, emoji: str) -> str:
        """
        Create ASCII table for network requests/responses.

        Args:
            section_name: Name of the section (e.g., "RESPONSES")
            entries: List of network entries
            emoji: Emoji indicator

        Returns:
            Formatted ASCII table
        """
        lines = []
        lines.append(f"─── {emoji} {section_name} ({len(entries)} entries) ───")
        lines.append("")

        # Table header
        lines.append(f"{'#':<4} {'METHOD':<8} {'URL':<60} {'STATUS':<8} {'DURATION':<12} {'SIZE':<12}")
        lines.append("─" * 120)

        for i, entry in enumerate(entries, 1):
            method = entry.get('method', 'GET')[:7]
            url = entry.get('url', '')[:58]  # Truncate very long URLs for table
            status = entry.get('status', entry.get('resource_type', 'N/A'))
            duration = entry.get('duration', 0)
            size = entry.get('size', 0)

            # Format status with emoji for HTTP codes
            status_str = str(status)
            if isinstance(status, int):
                if 200 <= status < 300:
                    status_str = f"✅ {status}"
                elif 300 <= status < 400:
                    status_str = f"↪️  {status}"
                elif 400 <= status < 500:
                    status_str = f"⚠️  {status}"
                elif status >= 500:
                    status_str = f"❌ {status}"

            # Format duration and size
            duration_str = f"{duration:.0f}ms" if duration else "N/A"
            size_str = self._format_bytes(size) if size else "N/A"

            lines.append(f"{i:<4} {method:<8} {url:<60} {status_str:<8} {duration_str:<12} {size_str:<12}")

        return "\n".join(lines)

    def _create_network_failed_table(self, section_name: str, entries: list, emoji: str) -> str:
        """
        Create ASCII table for failed network requests.

        Args:
            section_name: Name of the section (e.g., "FAILED REQUESTS")
            entries: List of failed request entries
            emoji: Emoji indicator

        Returns:
            Formatted ASCII table
        """
        lines = []
        lines.append(f"─── {emoji} {section_name} ({len(entries)} entries) ───")
        lines.append("")

        # Table header
        lines.append(f"{'#':<4} {'METHOD':<8} {'URL':<70} {'ERROR':<30}")
        lines.append("─" * 120)

        for i, entry in enumerate(entries, 1):
            method = entry.get('method', 'GET')[:7]
            url = entry.get('url', '')[:68]  # Truncate very long URLs
            error = entry.get('error', 'Unknown error')[:28]

            lines.append(f"{i:<4} {method:<8} {url:<70} {error:<30}")

        return "\n".join(lines)

    def _format_bytes(self, bytes_val: int) -> str:
        """
        Format bytes as human-readable string (KB, MB).

        Args:
            bytes_val: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 KB", "2.3 MB")
        """
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        else:
            return f"{bytes_val / (1024 * 1024):.1f} MB"

    def _format_console_data(self, console_data) -> str:
        """
        Format console data for logging with emoji severity indicators.

        Enhanced formatting:
        - 🔴 ERROR: Critical errors
        - 🟡 WARNING: Warnings
        - 🔵 INFO/LOG: Informational logs
        - ⚪ DEBUG: Debug logs
        - No truncation limits (show all logs)
        """
        try:
            if isinstance(console_data, list):
                if not console_data:
                    return "No console logs captured."

                # Group logs by severity
                errors = [log for log in console_data if log.get('type', '').lower() == 'error']
                warnings = [log for log in console_data if log.get('type', '').lower() == 'warning']
                info_logs = [log for log in console_data if log.get('type', '').lower() in ['info', 'log']]
                debug_logs = [log for log in console_data if log.get('type', '').lower() == 'debug']

                sections = []

                # Summary header
                sections.append("=" * 80)
                sections.append(f"CONSOLE LOGS SUMMARY ({len(console_data)} total entries)")
                sections.append("=" * 80)
                sections.append(f"🔴 Errors: {len(errors)}")
                sections.append(f"🟡 Warnings: {len(warnings)}")
                sections.append(f"🔵 Info/Log: {len(info_logs)}")
                sections.append(f"⚪ Debug: {len(debug_logs)}")
                sections.append("=" * 80)
                sections.append("")

                # Format each severity section
                if errors:
                    sections.append(self._format_console_section("ERRORS", errors, "🔴"))
                    sections.append("")

                if warnings:
                    sections.append(self._format_console_section("WARNINGS", warnings, "🟡"))
                    sections.append("")

                if info_logs:
                    sections.append(self._format_console_section("INFO/LOG", info_logs, "🔵"))
                    sections.append("")

                if debug_logs:
                    sections.append(self._format_console_section("DEBUG", debug_logs, "⚪"))
                    sections.append("")

                return "\n".join(sections).rstrip()
            return str(console_data)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Failed to format console data: {e}")
            return ""

    def _format_console_section(self, section_name: str, logs: list, emoji: str) -> str:
        """
        Format a section of console logs with consistent styling.

        Args:
            section_name: Name of the section (e.g., "ERRORS", "WARNINGS")
            logs: List of log entries
            emoji: Emoji indicator for severity

        Returns:
            Formatted section as string
        """
        lines = []
        lines.append(f"─── {emoji} {section_name} ({len(logs)} entries) ───")
        lines.append("")

        for i, log in enumerate(logs, 1):
            log_type = log.get('type', 'info')
            message = log.get('text', '')  # No truncation - show full message
            location = log.get('location', '')
            timestamp = log.get('timestamp', '')

            # Entry number and message
            lines.append(f"{emoji} [{i}] {message}")

            # Location and timestamp on separate lines for readability
            if location and location != 'unknown':
                lines.append(f"    📍 Location: {location}")
            lines.append(f"    ⏱  Time: {timestamp:.0f}ms")
            lines.append("")  # Empty line for separation

        return "\n".join(lines)

    def _get_collector_data(self, collector_type: str):
        """Get data from collectors."""
        try:
            # Try to get collector from environment manager directly
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()
            if env_manager and hasattr(env_manager, 'get_collector'):
                collector = env_manager.get_collector(collector_type)
                if collector:
                    # For console logs, get raw data instead of formatted text
                    if collector_type == 'console':
                        return collector.get_collected_data()
                    else:
                        return collector.get_data()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return None

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename by removing invalid characters."""
        import re
        return re.sub(r'[<>:"/\\|?*]', '_', name)

"""Console reporter for step-level reporting.

Responsibilities:
- Log console activity to ReportPortal
- Attach console logs as files
- Detect console errors
"""
from datetime import datetime
from typing import Any

from nemesis.infrastructure.logging import Logger
from .collectors_accessor import CollectorsAccessor
from .console_formatter import ConsoleDataFormatter


class ConsoleReporter:
    """Handles console activity logging and attachment for step reporting."""

    def __init__(self, collectors_accessor: CollectorsAccessor, formatter: ConsoleDataFormatter) -> None:
        """
        Initialize console reporter.

        Args:
            collectors_accessor: Accessor for collector data
            formatter: Console data formatter
        """
        self.logger = Logger.get_instance({})
        self.collectors = collectors_accessor
        self.formatter = formatter

    def log_console_activity(self, rp_client: Any, step_name: str) -> None:
        """
        Log console activity as step-level log in ReportPortal.

        Args:
            rp_client: ReportPortal client
            step_name: Name of the step
        """
        try:
            # Get console collector data
            console_collector = self.collectors.get_collector_data('console')
            if console_collector:
                # Format console data
                console_summary = self.formatter.format_console_data(console_collector)
                if console_summary:
                    # Check if there are errors in console output
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
                        rp_client.log_message(
                            f"Browser Console ({len(console_collector)} entries):\n\n{console_summary}",
                            "INFO"
                        )

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to log console activity: {e}",
                module=__name__,
                class_name="ConsoleReporter",
                method="log_console_activity"
            )

    def attach_console_logs(self, rp_client: Any, step_name: str) -> None:
        """
        Attach console logs as file attachment.

        Enhanced formatting with emoji severity indicators and no truncation limits.

        Args:
            rp_client: ReportPortal client
            step_name: Name of the step
        """
        try:
            # Get console collector data
            console_collector = self.collectors.get_collector_data('console')
            if console_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                name = f"console_logs_{timestamp}"

                # Use enhanced formatting method (shows all logs with emoji indicators)
                console_text = self.formatter.format_console_data(console_collector)

                rp_client.attach_file(
                    console_text.encode('utf-8'),
                    f"Console Logs: {step_name}",
                    "console_logs"
                )
                self.logger.debug(f"Console logs attached: {len(console_collector)} entries")

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to attach console logs: {e}",
                module=__name__,
                class_name="ConsoleReporter",
                method="attach_console_logs"
            )

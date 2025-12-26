"""Network reporter for step-level reporting.

Responsibilities:
- Log network activity to ReportPortal
- Attach network logs as files
- Detect network errors (4xx/5xx status codes)
"""
import json
from datetime import datetime
from typing import Any

from nemesis.infrastructure.logging import Logger
from .collectors_accessor import CollectorsAccessor
from .network_formatter import NetworkDataFormatter


class NetworkReporter:
    """Handles network activity logging and attachment for step reporting."""

    def __init__(self, collectors_accessor: CollectorsAccessor, formatter: NetworkDataFormatter) -> None:
        """
        Initialize network reporter.

        Args:
            collectors_accessor: Accessor for collector data
            formatter: Network data formatter
        """
        self.logger = Logger.get_instance({})
        self.collectors = collectors_accessor
        self.formatter = formatter

    def log_network_activity(self, rp_client: Any, step_name: str) -> None:
        """
        Log network activity as step-level log in ReportPortal.

        Args:
            rp_client: ReportPortal client
            step_name: Name of the step
        """
        try:
            # Get network collector data
            network_collector = self.collectors.get_collector_data('network')
            if network_collector:
                # Format network data
                network_summary = self.formatter.format_network_data(network_collector)
                if network_summary:
                    # Check if there are network errors (4xx, 5xx status codes)
                    has_errors = any(
                        req.get('status', 0) >= 400 for req in network_collector
                        if isinstance(req, dict)
                    ) if network_collector else False

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
                        rp_client.log_message(
                            f"Network Activity ({len(network_collector)} requests):\n\n{network_summary}",
                            "INFO"
                        )

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to log network activity: {e}",
                module=__name__,
                class_name="NetworkReporter",
                method="log_network_activity"
            )

    def attach_network_logs(self, rp_client: Any, step_name: str) -> None:
        """
        Attach network logs as file attachment.

        Args:
            rp_client: ReportPortal client
            step_name: Name of the step
        """
        try:
            # Get network collector data
            network_collector = self.collectors.get_collector_data('network')
            if network_collector:
                timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
                name = f"network_logs_{timestamp}"

                # Convert to JSON and attach
                network_json = json.dumps(network_collector, indent=2)
                rp_client.attach_file(
                    network_json.encode('utf-8'),
                    f"Network Logs: {step_name}",
                    "network_logs"
                )
                self.logger.debug(f"Network logs attached: {len(network_json)} bytes")

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to attach network logs: {e}",
                module=__name__,
                class_name="NetworkReporter",
                method="attach_network_logs"
            )

"""Collector content logging for ReportPortal."""
import json
import traceback
from pathlib import Path
from typing import Optional

from nemesis.infrastructure.logging import Logger
from nemesis.reporting.coordinator import ReportCoordinator


class CollectorContentLogger:
    """Logs collector file contents to ReportPortal for filtering and dashboards."""

    def __init__(self, report_manager: Optional[ReportCoordinator]) -> None:
        """Initialize collector content logger.

        Args:
            report_manager: Report manager instance
        """
        self.report_manager = report_manager
        self.logger = Logger.get_instance({})

    def log_console_content(self, console_file: Path) -> None:
        """Read console file and log complete content (same as local report structure)."""
        try:
            with open(console_file, 'r', encoding='utf-8') as f:
                file_content = f.read()

            if not file_content.strip():
                return

            # Log complete console content (same format as local report)
            # Split into chunks if too large (ReportPortal has message size limits)
            max_chunk_size = 9000  # Leave some room for prefix

            if len(file_content) <= max_chunk_size:
                self.report_manager.log_message(
                    f"[ATTACHMENT_TYPE:console] Console Logs:\n{file_content}",
                    "INFO"
                )
            else:
                # Split content into chunks
                lines = file_content.split('\n')
                chunk = []
                chunk_size = 0

                for line in lines:
                    line_with_newline = line + '\n'
                    if chunk_size + len(line_with_newline) > max_chunk_size and chunk:
                        # Log current chunk
                        chunk_content = ''.join(chunk)
                        self.report_manager.log_message(
                            f"[ATTACHMENT_TYPE:console] Console Logs (continued):\n{chunk_content}",
                            "INFO"
                        )
                        chunk = [line_with_newline]
                        chunk_size = len(line_with_newline)
                    else:
                        chunk.append(line_with_newline)
                        chunk_size += len(line_with_newline)

                # Log remaining chunk
                if chunk:
                    chunk_content = ''.join(chunk)
                    self.report_manager.log_message(
                        f"[ATTACHMENT_TYPE:console] Console Logs (continued):\n{chunk_content}",
                        "INFO"
                    )

        except (OSError, IOError, FileNotFoundError) as e:
            # File I/O errors - reading console file failed
            self.logger.warning(f"Failed to log console file content - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_console_content", console_file=str(console_file))
        except (AttributeError, RuntimeError) as e:
            # ReportPortal API errors - log_message failed
            self.logger.warning(f"Failed to log console file content - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_console_content", console_file=str(console_file))
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from file operations or ReportPortal
            # NOTE: File operations or report_manager.log_message may raise various exceptions we cannot predict
            self.logger.warning(f"Failed to log console file content: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_console_content", console_file=str(console_file))

    def log_network_content(self, network_file: Path) -> None:
        """Read network metrics file and log complete formatted content (same as local report)."""
        try:
            with open(network_file, 'r', encoding='utf-8') as f:
                network_data = json.load(f)

            # Format network data similar to local report formatter
            formatted_lines = []

            # Summary metrics
            total_requests = network_data.get('total_requests', 0)
            total_responses = network_data.get('total_responses', 0)
            total_failed = network_data.get('total_failed', 0)
            avg_duration = network_data.get('avg_duration_ms', 0)
            total_size = network_data.get('total_size_bytes', 0)

            formatted_lines.append("=" * 60)
            formatted_lines.append("NETWORK METRICS")
            formatted_lines.append("=" * 60)
            formatted_lines.append("")
            formatted_lines.append(f"Total Requests:    {total_requests}")
            formatted_lines.append(f"Total Responses:   {total_responses}")
            formatted_lines.append(f"Failed:            {total_failed}")
            formatted_lines.append(f"Avg Duration:      {avg_duration:.2f}ms")
            formatted_lines.append(f"Total Size:        {total_size / 1024:.2f}KB")
            formatted_lines.append("")

            # Status codes
            status_codes = network_data.get('status_codes', {})
            if status_codes:
                formatted_lines.append("Status Codes:")
                for code, count in sorted(status_codes.items()):
                    formatted_lines.append(f"  {code}: {count}")
                formatted_lines.append("")

            # Request details (group by method)
            requests = network_data.get('requests', [])
            if requests:
                by_method = {}
                for req in requests:
                    method = req.get('method', 'UNKNOWN')
                    if method not in by_method:
                        by_method[method] = []
                    by_method[method].append(req)

                formatted_lines.append("Requests by Method:")
                for method, reqs in sorted(by_method.items()):
                    formatted_lines.append(f"  {method}: {len(reqs)} requests")
                formatted_lines.append("")

                # Show request details (limit to prevent too many entries)
                formatted_lines.append("Request Details:")
                for i, req in enumerate(requests[:50]):  # Limit to first 50 requests
                    url = req.get('url', 'N/A')
                    method = req.get('method', 'GET')
                    status = req.get('status', 'N/A')
                    duration = req.get('duration', 0)
                    req_type = req.get('type', 'request')

                    formatted_lines.append(f"  [{i+1}] {method} {url}")
                    if req_type == 'response':
                        formatted_lines.append(f"       Status: {status}, Duration: {duration}ms")

                if len(requests) > 50:
                    formatted_lines.append(f"  ... and {len(requests) - 50} more requests (see attachment for full details)")

            # Join all lines and log (split into chunks if needed)
            formatted_content = '\n'.join(formatted_lines)
            max_chunk_size = 9000

            if len(formatted_content) <= max_chunk_size:
                self.report_manager.log_message(
                    f"[ATTACHMENT_TYPE:network] Network Metrics:\n{formatted_content}",
                    "INFO"
                )
            else:
                # Split into chunks
                chunks = [formatted_content[i:i+max_chunk_size] for i in range(0, len(formatted_content), max_chunk_size)]
                for i, chunk in enumerate(chunks):
                    prefix = "[ATTACHMENT_TYPE:network] Network Metrics" if i == 0 else "[ATTACHMENT_TYPE:network] Network Metrics (continued)"
                    self.report_manager.log_message(
                        f"{prefix}:\n{chunk}",
                        "INFO"
                    )

        except (OSError, IOError, FileNotFoundError) as e:
            # File I/O errors - reading network file failed
            self.logger.warning(f"Failed to log network file content - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_network_content", network_file=str(network_file))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # JSON parsing errors
            self.logger.warning(f"Failed to log network file content - JSON parse error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_network_content", network_file=str(network_file))
        except (AttributeError, RuntimeError) as e:
            # ReportPortal API errors - log_message failed
            self.logger.warning(f"Failed to log network file content - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_network_content", network_file=str(network_file))
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from file operations or ReportPortal
            # NOTE: File operations, JSON parsing, or report_manager.log_message may raise various exceptions we cannot predict
            self.logger.warning(f"Failed to log network file content: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_network_content", network_file=str(network_file))

    def log_performance_content(self, performance_file: Path) -> None:
        """Read performance metrics file and log complete formatted content (same as local report)."""
        try:
            with open(performance_file, 'r', encoding='utf-8') as f:
                performance_data = json.load(f)

            # Format performance data similar to local report formatter
            formatted_lines = []

            formatted_lines.append("=" * 60)
            formatted_lines.append("PERFORMANCE METRICS")
            formatted_lines.append("=" * 60)
            formatted_lines.append("")

            if isinstance(performance_data, dict):
                # Navigation timing
                if 'navigation' in performance_data:
                    nav = performance_data['navigation']
                    if isinstance(nav, dict):
                        formatted_lines.append("Navigation Timing:")
                        formatted_lines.append(f"  DNS Lookup:       {nav.get('dns_time', 0):.2f}ms")
                        formatted_lines.append(f"  TCP Connection:   {nav.get('tcp_time', 0):.2f}ms")
                        formatted_lines.append(f"  TTFB:             {nav.get('ttfb', 0):.2f}ms")
                        formatted_lines.append(f"  Download:         {nav.get('download_time', 0):.2f}ms")
                        formatted_lines.append(f"  DOM Processing:   {nav.get('dom_processing_time', 0):.2f}ms")
                        formatted_lines.append(f"  Total Load Time:  {nav.get('total_load_time', 0):.2f}ms")
                        formatted_lines.append("")

                # Paint metrics
                if 'paint' in performance_data:
                    paint = performance_data['paint']
                    if isinstance(paint, dict):
                        formatted_lines.append("Paint Metrics:")
                        # Try both underscore and dash formats for compatibility
                        first_paint = paint.get('first_paint') or paint.get('first-paint')
                        if first_paint:
                            formatted_lines.append(f"  First Paint:      {first_paint:.2f}ms")
                        first_contentful_paint = paint.get('first_contentful_paint') or paint.get('first-contentful-paint')
                        if first_contentful_paint:
                            formatted_lines.append(f"  First Contentful Paint: {first_contentful_paint:.2f}ms")
                        formatted_lines.append("")

                # Web Vitals (try both underscore and camelCase formats)
                vitals = performance_data.get('web_vitals') or performance_data.get('webVitals')
                if vitals and isinstance(vitals, dict):
                    formatted_lines.append("Web Vitals:")
                    for vital_name, vital_value in sorted(vitals.items()):
                        if vital_name.endswith('_status') or vital_name.endswith('Status'):
                            continue
                        if isinstance(vital_value, (int, float)):
                            formatted_lines.append(f"  {vital_name}: {vital_value:.2f}")
                    formatted_lines.append("")

                # Memory metrics
                if 'memory' in performance_data:
                    mem = performance_data['memory']
                    if isinstance(mem, dict):
                        formatted_lines.append("Memory Usage:")
                        formatted_lines.append(f"  Used JS Heap:     {mem.get('used_js_heap_size_mb', 0):.2f} MB")
                        formatted_lines.append(f"  Total JS Heap:    {mem.get('total_js_heap_size_mb', 0):.2f} MB")
                        formatted_lines.append(f"  Heap Usage:       {mem.get('heap_usage_percent', 0):.2f}%")
                        formatted_lines.append("")

                # Resource summary
                if 'resource_summary' in performance_data:
                    res_summary = performance_data['resource_summary']
                    if isinstance(res_summary, dict):
                        formatted_lines.append("Resource Summary:")
                        formatted_lines.append(f"  Total Count:      {res_summary.get('total_count', 0)}")
                        formatted_lines.append(f"  Total Transfer:   {res_summary.get('total_transfer_size', 0) / 1024:.2f}KB")
                        formatted_lines.append(f"  Total Duration:   {res_summary.get('total_duration', 0):.2f}ms")
                        formatted_lines.append("")

            # Join all lines and log (split into chunks if needed)
            formatted_content = '\n'.join(formatted_lines)
            max_chunk_size = 9000

            if len(formatted_content) <= max_chunk_size:
                self.report_manager.log_message(
                    f"[ATTACHMENT_TYPE:performance] Performance Metrics:\n{formatted_content}",
                    "INFO"
                )
            else:
                # Split into chunks
                chunks = [formatted_content[i:i+max_chunk_size] for i in range(0, len(formatted_content), max_chunk_size)]
                for i, chunk in enumerate(chunks):
                    prefix = "[ATTACHMENT_TYPE:performance] Performance Metrics" if i == 0 else "[ATTACHMENT_TYPE:performance] Performance Metrics (continued)"
                    self.report_manager.log_message(
                        f"{prefix}:\n{chunk}",
                        "INFO"
                    )

        except (OSError, IOError, FileNotFoundError) as e:
            # File I/O errors - reading performance file failed
            self.logger.warning(f"Failed to log performance file content - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_performance_content", performance_file=str(performance_file))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # JSON parsing errors
            self.logger.warning(f"Failed to log performance file content - JSON parse error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_performance_content", performance_file=str(performance_file))
        except (AttributeError, RuntimeError) as e:
            # ReportPortal API errors - log_message failed
            self.logger.warning(f"Failed to log performance file content - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_performance_content", performance_file=str(performance_file))
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from file operations or ReportPortal
            # NOTE: File operations, JSON parsing, or report_manager.log_message may raise various exceptions we cannot predict
            self.logger.warning(f"Failed to log performance file content: {e}", traceback=traceback.format_exc(), module=__name__, class_name="CollectorContentLogger", method="log_performance_content", performance_file=str(performance_file))

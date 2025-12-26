"""Network data formatter for step reporting.

Responsibilities:
- Format network request/response data as ASCII tables
- Group network events by type (responses, requests, failed)
- Format bytes to human-readable format
"""
from typing import Any, List

from nemesis.infrastructure.logging import Logger


class NetworkDataFormatter:
    """Formats network data for reporting with enhanced readability."""

    def __init__(self) -> None:
        """Initialize network data formatter."""
        self.logger = Logger.get_instance({})

    def format_network_data(self, network_data: Any) -> str:
        """
        Format network data as ASCII table with enhanced readability.

        Creates a structured table with:
        - Method | URL | Status | Duration | Size | Type
        - No truncation limits (shows all requests)
        - Grouped by request type (responses, requests, failed)

        Args:
            network_data: List of network events

        Returns:
            Formatted network data string
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

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to format network data: {e}",
                module=__name__,
                class_name="NetworkDataFormatter",
                method="format_network_data"
            )
            return ""

    def _create_network_table(self, section_name: str, entries: List[dict], emoji: str) -> str:
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

    def _create_network_failed_table(self, section_name: str, entries: List[dict], emoji: str) -> str:
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

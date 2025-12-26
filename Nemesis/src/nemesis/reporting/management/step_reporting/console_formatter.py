"""Console data formatter for step reporting.

Responsibilities:
- Format console log data with emoji severity indicators
- Group logs by severity (error, warning, info, debug)
- Create readable console log sections
"""
from typing import Any, List

from nemesis.infrastructure.logging import Logger


class ConsoleDataFormatter:
    """Formats console data for reporting with emoji severity indicators."""

    def __init__(self) -> None:
        """Initialize console data formatter."""
        self.logger = Logger.get_instance({})

    def format_console_data(self, console_data: Any) -> str:
        """
        Format console data for logging with emoji severity indicators.

        Enhanced formatting:
        - 🔴 ERROR: Critical errors
        - 🟡 WARNING: Warnings
        - 🔵 INFO/LOG: Informational logs
        - ⚪ DEBUG: Debug logs
        - No truncation limits (show all logs)

        Args:
            console_data: List of console log entries

        Returns:
            Formatted console data string
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

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.warning(
                f"Failed to format console data: {e}",
                module=__name__,
                class_name="ConsoleDataFormatter",
                method="format_console_data"
            )
            return ""

    def _format_console_section(self, section_name: str, logs: List[dict], emoji: str) -> str:
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

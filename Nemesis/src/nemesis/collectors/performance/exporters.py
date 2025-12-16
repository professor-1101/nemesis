"""Performance report exporters."""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .models import PerformanceReport


class BaseExporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(self, report: PerformanceReport, output: Any) -> None:
        """Export report to output."""


class JSONExporter(BaseExporter):
    """Export performance report to JSON file."""

    def export(self, report: PerformanceReport, output: Path) -> None:
        """
        Export report to JSON file.

        :param report: Performance report
        :param output: Output file path
        """
        output.parent.mkdir(parents=True, exist_ok=True)

        data = report.to_dict()

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class SummaryExporter(BaseExporter):
    """Export performance report as human-readable summary."""

    def export(self, report: PerformanceReport, output: Any = None) -> str:
        """
        Generate human-readable summary.

        :param report: Performance report
        :param output: Optional output file path
        :return: Formatted summary string
        """
        lines = self._build_summary_lines(report)
        summary = '\n'.join(lines)

        if output:
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w', encoding='utf-8') as f:
                f.write(summary)

        return summary

    def _build_summary_lines(self, report: PerformanceReport) -> list[str]:
        """Build summary text lines."""
        lines = [
            "=" * 80,
            "PERFORMANCE METRICS SUMMARY",
            "=" * 80,
            "",
        ]

        # Core Web Vitals
        if report.web_vitals:
            lines.extend(self._format_web_vitals(report.web_vitals))

        # Navigation Timing
        if report.navigation:
            lines.extend(self._format_navigation(report.navigation))

        # Resources
        if report.resource_summary and report.resource_summary.total_count > 0:
            lines.extend(self._format_resources(report.resource_summary))

        # Paint Timing
        if report.paint:
            lines.extend(self._format_paint(report.paint))

        # Memory
        if report.memory and report.memory.used_js_heap_size > 0:
            lines.extend(self._format_memory(report.memory))

        # Long Tasks
        if report.long_tasks:
            lines.extend(self._format_long_tasks(report.long_tasks))

        # Layout Shifts
        if report.layout_shifts:
            lines.extend(self._format_layout_shifts(report.layout_shifts))

        # Runtime
        if report.runtime:
            lines.extend(self._format_runtime(report.runtime))

        lines.append("=" * 80)
        return lines

    def _format_web_vitals(self, vitals: Any) -> list[str]:
        """Format Core Web Vitals section."""
        return [
            "CORE WEB VITALS",
            "-" * 80,
            f"  LCP (Largest Contentful Paint): {vitals.lcp:.0f}ms [{vitals.lcp_status}]",
            "    → Target: ≤ 2500ms (good), ≤ 4000ms (needs improvement)",
            f"  INP (Interaction to Next Paint): {vitals.inp:.0f}ms [{vitals.inp_status}]",
            "    → Target: ≤ 200ms (good), ≤ 500ms (needs improvement)",
            f"  CLS (Cumulative Layout Shift): {vitals.cls:.3f} [{vitals.cls_status}]",
            "    → Target: ≤ 0.1 (good), ≤ 0.25 (needs improvement)",
            "",
            "  Additional Metrics:",
            f"    FCP (First Contentful Paint): {vitals.fcp:.0f}ms",
            f"    TTI (Time to Interactive): {vitals.tti:.0f}ms",
            f"    TBT (Total Blocking Time): {vitals.tbt:.0f}ms",
            "",
        ]

    def _format_navigation(self, nav: Any) -> list[str]:
        """Format Navigation Timing section."""
        return [
            "NAVIGATION TIMING",
            "-" * 80,
            f"  Total Page Load: {nav.total_load_time:.0f}ms",
            f"  DNS Lookup: {nav.dns_time:.0f}ms",
            f"  TCP Connection: {nav.tcp_time:.0f}ms",
            f"  TTFB (Time to First Byte): {nav.ttfb:.0f}ms",
            f"  Download Time: {nav.download_time:.0f}ms",
            f"  DOM Processing: {nav.dom_processing_time:.0f}ms",
            f"  Transfer Size: {nav.transfer_size / 1024:.2f}KB",
            f"  Navigation Type: {nav.type}",
            "",
        ]

    def _format_resources(self, summary: Any) -> list[str]:
        """Format Resources section."""
        lines = [
            "RESOURCES",
            "-" * 80,
            f"  Total Resources: {summary.total_count}",
            f"  Total Transfer Size: {summary.total_transfer_size / 1024:.2f}KB",
            f"  Total Decoded Size: {summary.total_decoded_size / 1024:.2f}KB",
            f"  Cache Hit Ratio: {summary.cache_hit_ratio * 100:.1f}%",
            "",
            "  By Type:",
        ]

        for res_type, data in summary.by_type.items():
            lines.append(
                f"    {res_type}: {data['count']} resources, "
                f"{data['totalSize'] / 1024:.2f}KB, "
                f"avg {data['avgDuration']:.2f}ms"
            )

        if summary.largest_resources:
            lines.append("")
            lines.append("  Largest Resources (Top 5):")
            for i, res in enumerate(summary.largest_resources[:5], 1):
                name = res.name.split('/')[-1][:50]  # Last part, max 50 chars
                lines.append(
                    f"    {i}. {name} - {res.transfer_size / 1024:.2f}KB "
                    f"({res.duration:.2f}ms)"
                )

        lines.append("")
        return lines

    def _format_paint(self, paint: Any) -> list[str]:
        """Format Paint Timing section."""
        return [
            "PAINT TIMING",
            "-" * 80,
            f"  First Paint (FP): {paint.first_paint:.0f}ms",
            f"  First Contentful Paint (FCP): {paint.first_contentful_paint:.0f}ms",
            "",
        ]

    def _format_memory(self, memory: Any) -> list[str]:
        """Format Memory section."""
        return [
            "MEMORY USAGE",
            "-" * 80,
            f"  Used JS Heap: {memory.used_js_heap_size_mb:.2f}MB ({memory.heap_usage_percent:.1f}%)",
            f"  Total JS Heap: {memory.total_js_heap_size_mb:.2f}MB",
            f"  Heap Limit: {memory.js_heap_size_limit / 1048576:.2f}MB",
            "",
        ]

    def _format_long_tasks(self, tasks: list) -> list[str]:
        """Format Long Tasks section."""
        if not tasks:
            return []

        total_blocking = sum(max(0, t.duration - 50) for t in tasks)
        return [
            "LONG TASKS (≥ 50ms)",
            "-" * 80,
            f"  Total Long Tasks: {len(tasks)}",
            f"  Total Blocking Time: {total_blocking:.0f}ms",
            f"  Longest Task: {max(t.duration for t in tasks):.0f}ms",
            "",
            "  Top 5 Long Tasks:",
            *[
                f"    {i}. {t.name}: {t.duration:.0f}ms at {t.start_time:.0f}ms"
                for i, t in enumerate(sorted(tasks, key=lambda x: x.duration, reverse=True)[:5], 1)
            ],
            "",
        ]

    def _format_layout_shifts(self, shifts: list) -> list[str]:
        """Format Layout Shifts section."""
        if not shifts:
            return []

        unexpected_shifts = [s for s in shifts if not s.had_recent_input]
        total_cls = sum(s.value for s in unexpected_shifts)

        return [
            "LAYOUT SHIFTS",
            "-" * 80,
            f"  Total Shifts: {len(shifts)}",
            f"  Unexpected Shifts: {len(unexpected_shifts)}",
            f"  Cumulative Layout Shift: {total_cls:.3f}",
            "",
        ]

    def _format_runtime(self, runtime: Any) -> list[str]:
        """Format Runtime Metrics section."""
        return [
            "RUNTIME PERFORMANCE",
            "-" * 80,
            f"  Estimated FPS: {runtime.fps}",
            f"  Jank Count (frames > 50ms): {runtime.jank_count}",
            f"  Average Frame Time: {runtime.average_frame_time:.2f}ms",
            f"  Longest Frame: {runtime.longest_frame:.2f}ms",
            "",
        ]

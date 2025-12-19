"""Memory metrics collector."""
from ..models import MemoryMetrics
from .base import BaseMetricCollector


class MemoryCollector(BaseMetricCollector):
    """Collects memory usage metrics (Chrome-specific)."""

    def collect(self) -> MemoryMetrics:
        """Collect memory metrics."""
        raw_data = self._safe_evaluate(self._get_script(), {})

        if not raw_data:
            return MemoryMetrics()

        used_mb = raw_data.get('usedJSHeapSizeMB', 0)
        total_mb = raw_data.get('totalJSHeapSizeMB', 0)

        return MemoryMetrics(
            used_js_heap_size=raw_data.get('usedJSHeapSize', 0),
            total_js_heap_size=raw_data.get('totalJSHeapSize', 0),
            js_heap_size_limit=raw_data.get('jsHeapSizeLimit', 0),
            used_js_heap_size_mb=used_mb,
            total_js_heap_size_mb=total_mb,
            heap_usage_percent=round((used_mb / total_mb * 100), 2) if total_mb > 0 else 0,
        )

    def _get_script(self) -> str:
        return """() => {
            if (!performance.memory) return {};
            return {
                usedJSHeapSize: performance.memory.usedJSHeapSize,
                totalJSHeapSize: performance.memory.totalJSHeapSize,
                jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                usedJSHeapSizeMB: Math.round(performance.memory.usedJSHeapSize / 1048576 * 100) / 100,
                totalJSHeapSizeMB: Math.round(performance.memory.totalJSHeapSize / 1048576 * 100) / 100
            };
        }"""

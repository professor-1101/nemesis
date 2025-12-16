"""Runtime metrics collector."""
from ..models import RuntimeMetrics
from .base import BaseMetricCollector


class RuntimeMetricsCollector(BaseMetricCollector):
    """Collects runtime performance metrics (FPS, frames)."""

    def collect(self) -> RuntimeMetrics:
        """
        Collect runtime metrics.

        Note: FPS/frame metrics require DevTools Protocol or
        continuous monitoring. This provides a snapshot estimation.
        """
        raw_data = self._safe_evaluate(self._get_script(), {})

        return RuntimeMetrics(
            fps=raw_data.get('estimatedFps', 0),
            dropped_frames=0,  # Requires CDP
            total_frames=0,  # Requires CDP
            jank_count=raw_data.get('jankCount', 0),
            average_frame_time=raw_data.get('avgFrameTime', 0),
            longest_frame=raw_data.get('longestFrame', 0),
        )

    def _get_script(self) -> str:
        return """() => {
            // Estimate based on long tasks
            const longTasks = performance.getEntriesByType('longtask');
            const jankCount = longTasks.filter(t => t.duration > 50).length;

            // Very rough FPS estimate
            const navEntry = performance.getEntriesByType('navigation')[0];
            const totalTime = navEntry ? navEntry.loadEventEnd : 0;
            const estimatedFrames = totalTime / 16.67; // 60fps baseline
            const estimatedFps = estimatedFrames > 0 ? Math.round(60 - (jankCount / estimatedFrames * 60)) : 0;

            return {
                estimatedFps: Math.max(0, estimatedFps),
                jankCount: jankCount,
                avgFrameTime: longTasks.length > 0 ?
                    Math.round(longTasks.reduce((sum, t) => sum + t.duration, 0) / longTasks.length) : 0,
                longestFrame: longTasks.length > 0 ?
                    Math.round(Math.max(...longTasks.map(t => t.duration))) : 0
            };
        }"""

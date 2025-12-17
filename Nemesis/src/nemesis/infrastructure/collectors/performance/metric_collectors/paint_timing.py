"""Paint timing metrics collector."""
from ..models import PaintTiming
from .base import BaseMetricCollector


class PaintTimingCollector(BaseMetricCollector):
    """Collects paint timing metrics (FP, FCP)."""

    def collect(self) -> PaintTiming:
        """Collect paint timing metrics."""
        raw_data = self._safe_evaluate(self._get_script(), {})

        return PaintTiming(
            first_paint=self._round_metric(raw_data.get('first-paint', 0)),
            first_contentful_paint=self._round_metric(
                raw_data.get('first-contentful-paint', 0)
            ),
        )

    def _get_script(self) -> str:
        return """() => {
            const paintEntries = performance.getEntriesByType('paint');
            const result = {};
            paintEntries.forEach(entry => {
                result[entry.name] = entry.startTime;
            });
            return result;
        }"""

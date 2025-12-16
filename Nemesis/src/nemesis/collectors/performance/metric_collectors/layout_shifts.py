"""Layout shifts collector."""
from ..models import LayoutShift
from .base import BaseMetricCollector


class LayoutShiftsCollector(BaseMetricCollector):
    """Collects layout shift entries."""

    def collect(self) -> list[LayoutShift]:
        """Collect layout shifts."""
        raw_shifts = self._safe_evaluate(self._get_script(), [])

        shifts = []
        for s in raw_shifts:
            shift = LayoutShift(
                value=self._round_metric(s.get('value', 0), 3),
                start_time=self._round_metric(s.get('startTime', 0)),
                had_recent_input=s.get('hadRecentInput', False),
                sources=s.get('sources', []),
            )
            shifts.append(shift)

        return shifts

    def _get_script(self) -> str:
        return """() => {
            try {
                const layoutShifts = performance.getEntriesByType('layout-shift');
                return layoutShifts.map(s => ({
                    value: s.value,
                    startTime: s.startTime,
                    hadRecentInput: s.hadRecentInput,
                    sources: s.sources ? s.sources.map(src => ({
                        node: src.node ? {
                            tagName: src.node.tagName,
                            id: src.node.id,
                            className: src.node.className
                        } : null,
                        previousRect: src.previousRect,
                        currentRect: src.currentRect
                    })) : []
                }));
            } catch (e) {
                return [];
            }
        }"""

"""Event timing collector."""
from ..models import EventTiming
from .base import BaseMetricCollector


class EventTimingCollector(BaseMetricCollector):
    """Collects event timing entries."""

    def collect(self) -> list[EventTiming]:
        """Collect event timing entries."""
        raw_events = self._safe_evaluate(self._get_script(), [])

        events = []
        for e in raw_events:
            event = EventTiming(
                name=e.get('name', ''),
                duration=self._round_metric(e.get('duration', 0)),
                processing_start=self._round_metric(e.get('processingStart', 0)),
                processing_end=self._round_metric(e.get('processingEnd', 0)),
                start_time=self._round_metric(e.get('startTime', 0)),
                cancelable=e.get('cancelable', False),
                target=e.get('target', ''),
            )
            events.append(event)

        return events

    def _get_script(self) -> str:
        return """() => {
            try {
                const eventEntries = performance.getEntriesByType('event');
                return eventEntries.map(e => ({
                    name: e.name,
                    duration: e.duration,
                    processingStart: e.processingStart,
                    processingEnd: e.processingEnd,
                    startTime: e.startTime,
                    cancelable: e.cancelable,
                    target: e.target ? e.target.tagName || 'unknown' : 'unknown'
                }));
            } catch (e) {
                return [];
            }
        }"""

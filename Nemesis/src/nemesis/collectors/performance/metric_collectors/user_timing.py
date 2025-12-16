"""User timing collector."""
from ..models import UserTimingEntry
from .base import BaseMetricCollector


class UserTimingCollector(BaseMetricCollector):
    """Collects user timing marks and measures."""

    def collect(self) -> list[UserTimingEntry]:
        """Collect user timing entries."""
        raw_entries = self._safe_evaluate(self._get_script(), [])

        entries = []
        for e in raw_entries:
            entry = UserTimingEntry(
                name=e.get('name', ''),
                entry_type=e.get('entryType', 'mark'),
                start_time=self._round_metric(e.get('startTime', 0)),
                duration=self._round_metric(e.get('duration', 0)),
            )
            entries.append(entry)

        return entries

    def _get_script(self) -> str:
        return """() => {
            try {
                const userTiming = performance.getEntriesByType('measure');
                const marks = performance.getEntriesByType('mark');

                const allEntries = [...userTiming, ...marks];
                return allEntries.map(e => ({
                    name: e.name,
                    entryType: e.entryType,
                    startTime: e.startTime,
                    duration: e.duration || 0
                }));
            } catch (e) {
                return [];
            }
        }"""

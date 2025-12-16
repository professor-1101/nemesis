"""Long tasks collector."""
from ..models import LongTask
from .base import BaseMetricCollector


class LongTasksCollector(BaseMetricCollector):
    """Collects long task entries (>= 50ms)."""

    def collect(self) -> list[LongTask]:
        """Collect long tasks."""
        raw_tasks = self._safe_evaluate(self._get_script(), [])

        tasks = []
        for t in raw_tasks:
            task = LongTask(
                name=t.get('name', 'unknown'),
                duration=self._round_metric(t.get('duration', 0)),
                start_time=self._round_metric(t.get('startTime', 0)),
                attribution=t.get('attribution', []),
            )
            tasks.append(task)

        return tasks

    def _get_script(self) -> str:
        return """() => {
            try {
                const longTasks = performance.getEntriesByType('longtask');
                return longTasks.map(t => ({
                    name: t.name,
                    duration: t.duration,
                    startTime: t.startTime,
                    attribution: t.attribution ? t.attribution.map(a => ({
                        name: a.name,
                        containerType: a.containerType,
                        containerId: a.containerId,
                        containerName: a.containerName
                    })) : []
                }));
            } catch (e) {
                return [];
            }
        }"""

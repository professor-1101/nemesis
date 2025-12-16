"""Resource timing metrics collector."""
from ..models import ResourceTiming, ResourceSummary
from .base import BaseMetricCollector


class ResourceTimingCollector(BaseMetricCollector):
    """Collects resource timing for all loaded resources."""

    def collect(self) -> list[ResourceTiming]:
        """Collect resource timing for all resources."""
        raw_resources = self._safe_evaluate(self._get_script(), [])

        resources = []
        for r in raw_resources:
            resource = ResourceTiming(
                name=r.get('name', ''),
                duration=self._round_metric(r.get('duration', 0)),
                transfer_size=r.get('transferSize', 0),
                encoded_body_size=r.get('encodedBodySize', 0),
                decoded_body_size=r.get('decodedBodySize', 0),
                initiator_type=r.get('initiatorType', 'other'),
                start_time=self._round_metric(r.get('startTime', 0)),
                response_end=self._round_metric(r.get('responseEnd', 0)),
                fetch_start=self._round_metric(r.get('fetchStart', 0)),
                domain_lookup_start=self._round_metric(r.get('domainLookupStart', 0)),
                domain_lookup_end=self._round_metric(r.get('domainLookupEnd', 0)),
                connect_start=self._round_metric(r.get('connectStart', 0)),
                connect_end=self._round_metric(r.get('connectEnd', 0)),
                request_start=self._round_metric(r.get('requestStart', 0)),
                response_start=self._round_metric(r.get('responseStart', 0)),
                cache_hit=r.get('transferSize', 0) == 0 and r.get('decodedBodySize', 0) > 0,
            )
            resources.append(resource)

        return resources

    def calculate_summary(self, resources: list[ResourceTiming]) -> ResourceSummary:
        """Calculate summary statistics for resources."""
        if not resources:
            return ResourceSummary()

        summary = ResourceSummary(
            total_count=len(resources),
            total_transfer_size=sum(r.transfer_size for r in resources),
            total_encoded_size=sum(r.encoded_body_size for r in resources),
            total_decoded_size=sum(r.decoded_body_size for r in resources),
            total_duration=sum(r.duration for r in resources),
        )

        # Group by type
        by_type: dict[str, dict[str, any]] = {}
        for resource in resources:
            r_type = resource.initiator_type or 'other'
            if r_type not in by_type:
                by_type[r_type] = {
                    'count': 0,
                    'totalSize': 0,
                    'totalDuration': 0,
                    'avgSize': 0,
                    'avgDuration': 0,
                }

            by_type[r_type]['count'] += 1
            by_type[r_type]['totalSize'] += resource.transfer_size
            by_type[r_type]['totalDuration'] += resource.duration

        # Calculate averages
        for r_type in by_type:
            count = by_type[r_type]['count']
            by_type[r_type]['avgSize'] = round(by_type[r_type]['totalSize'] / count, 2)
            by_type[r_type]['avgDuration'] = round(by_type[r_type]['totalDuration'] / count, 2)

        summary.by_type = by_type

        # Cache hit ratio
        cache_hits = sum(1 for r in resources if r.cache_hit)
        summary.cache_hit_ratio = round(cache_hits / len(resources), 3) if resources else 0

        # Largest resources (top 10)
        sorted_resources = sorted(resources, key=lambda r: r.transfer_size, reverse=True)
        summary.largest_resources = sorted_resources[:10]

        return summary

    def _get_script(self) -> str:
        """Get JavaScript for collecting resource timing."""
        return """() => {
            const resources = performance.getEntriesByType('resource');
            return resources.map(r => ({
                name: r.name,
                duration: r.duration,
                transferSize: r.transferSize || 0,
                encodedBodySize: r.encodedBodySize || 0,
                decodedBodySize: r.decodedBodySize || 0,
                initiatorType: r.initiatorType || 'other',
                startTime: r.startTime,
                responseEnd: r.responseEnd,
                fetchStart: r.fetchStart,
                domainLookupStart: r.domainLookupStart || 0,
                domainLookupEnd: r.domainLookupEnd || 0,
                connectStart: r.connectStart || 0,
                connectEnd: r.connectEnd || 0,
                requestStart: r.requestStart || 0,
                responseStart: r.responseStart || 0
            }));
        }"""

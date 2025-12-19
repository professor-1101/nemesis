"""Navigation timing metrics collector."""
from ..models import NavigationTiming
from .base import BaseMetricCollector


class NavigationTimingCollector(BaseMetricCollector):
    """Collects navigation timing metrics using Performance API."""

    def collect(self) -> NavigationTiming:
        """
        Collect navigation timing metrics.

        Returns both modern PerformanceNavigationTiming and legacy fallback.
        """
        raw_data = self._safe_evaluate(self._get_script(), {})

        if not raw_data:
            return NavigationTiming()

        timing = NavigationTiming(
            fetch_start=raw_data.get('fetchStart', 0),
            domain_lookup_start=raw_data.get('domainLookupStart', 0),
            domain_lookup_end=raw_data.get('domainLookupEnd', 0),
            connect_start=raw_data.get('connectStart', 0),
            connect_end=raw_data.get('connectEnd', 0),
            secure_connection_start=raw_data.get('secureConnectionStart', 0),
            request_start=raw_data.get('requestStart', 0),
            response_start=raw_data.get('responseStart', 0),
            response_end=raw_data.get('responseEnd', 0),
            dom_interactive=raw_data.get('domInteractive', 0),
            dom_content_loaded_start=raw_data.get('domContentLoadedEventStart', 0),
            dom_content_loaded_end=raw_data.get('domContentLoadedEventEnd', 0),
            dom_complete=raw_data.get('domComplete', 0),
            load_event_start=raw_data.get('loadEventStart', 0),
            load_event_end=raw_data.get('loadEventEnd', 0),
            transfer_size=raw_data.get('transferSize', 0),
            encoded_body_size=raw_data.get('encodedBodySize', 0),
            decoded_body_size=raw_data.get('decodedBodySize', 0),
            redirect_count=raw_data.get('redirectCount', 0),
            type=raw_data.get('type', ''),
        )

        # Calculate derived metrics
        timing.dns_time = self._round_metric(
            timing.domain_lookup_end - timing.domain_lookup_start
        )
        timing.tcp_time = self._round_metric(
            timing.connect_end - timing.connect_start
        )
        timing.ttfb = self._round_metric(
            timing.response_start - timing.request_start
        )
        timing.download_time = self._round_metric(
            timing.response_end - timing.response_start
        )
        timing.dom_processing_time = self._round_metric(
            timing.dom_complete - timing.dom_interactive
        )
        timing.total_load_time = self._round_metric(timing.load_event_end)

        return timing

    def _get_script(self) -> str:
        """Get JavaScript for collecting navigation timing."""
        return """() => {
            // Try modern API first
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                return {
                    fetchStart: perfData.fetchStart,
                    domainLookupStart: perfData.domainLookupStart,
                    domainLookupEnd: perfData.domainLookupEnd,
                    connectStart: perfData.connectStart,
                    connectEnd: perfData.connectEnd,
                    secureConnectionStart: perfData.secureConnectionStart,
                    requestStart: perfData.requestStart,
                    responseStart: perfData.responseStart,
                    responseEnd: perfData.responseEnd,
                    domInteractive: perfData.domInteractive,
                    domContentLoadedEventStart: perfData.domContentLoadedEventStart,
                    domContentLoadedEventEnd: perfData.domContentLoadedEventEnd,
                    domComplete: perfData.domComplete,
                    loadEventStart: perfData.loadEventStart,
                    loadEventEnd: perfData.loadEventEnd,
                    transferSize: perfData.transferSize || 0,
                    encodedBodySize: perfData.encodedBodySize || 0,
                    decodedBodySize: perfData.decodedBodySize || 0,
                    redirectCount: perfData.redirectCount || 0,
                    type: perfData.type || 'navigate'
                };
            }

            // Fallback to legacy API
            const timing = performance.timing;
            const nav = timing.navigationStart;
            return {
                fetchStart: 0,
                domainLookupStart: timing.domainLookupStart - nav,
                domainLookupEnd: timing.domainLookupEnd - nav,
                connectStart: timing.connectStart - nav,
                connectEnd: timing.connectEnd - nav,
                secureConnectionStart: timing.secureConnectionStart - nav,
                requestStart: timing.requestStart - nav,
                responseStart: timing.responseStart - nav,
                responseEnd: timing.responseEnd - nav,
                domInteractive: timing.domInteractive - nav,
                domContentLoadedEventStart: timing.domContentLoadedEventStart - nav,
                domContentLoadedEventEnd: timing.domContentLoadedEventEnd - nav,
                domComplete: timing.domComplete - nav,
                loadEventStart: timing.loadEventStart - nav,
                loadEventEnd: timing.loadEventEnd - nav,
                transferSize: 0,
                encodedBodySize: 0,
                decodedBodySize: 0,
                redirectCount: performance.navigation?.redirectCount || 0,
                type: 'navigate'
            };
        }"""

"""Core Web Vitals collector."""
from ..models import WebVitals
from .base import BaseMetricCollector


class WebVitalsCollector(BaseMetricCollector):
    """
    Collects Core Web Vitals metrics.

    Metrics collected:
    - LCP (Largest Contentful Paint) - Target: ≤ 2.5s
    - INP (Interaction to Next Paint) - Target: ≤ 200ms
    - CLS (Cumulative Layout Shift) - Target: ≤ 0.1
    - FCP (First Contentful Paint)
    - TTI (Time to Interactive)
    - TBT (Total Blocking Time)
    """

    def collect(self) -> WebVitals:
        """Collect Core Web Vitals and related metrics."""
        raw_data = self._safe_evaluate(self._get_script(), {})

        if not raw_data:
            return WebVitals()

        vitals = WebVitals(
            lcp=raw_data.get('lcp', 0),
            inp=raw_data.get('inp', 0),
            cls=self._round_metric(raw_data.get('cls', 0), 3),
            fcp=raw_data.get('fcp', 0),
            tti=raw_data.get('tti', 0),
            tbt=raw_data.get('tbt', 0),
            fid=raw_data.get('fid', 0),
        )

        # Calculate status based on Google thresholds
        vitals.lcp_status = self._get_lcp_status(vitals.lcp)
        vitals.inp_status = self._get_inp_status(vitals.inp)
        vitals.cls_status = self._get_cls_status(vitals.cls)

        return vitals

    def _get_lcp_status(self, lcp: float) -> str:
        """Get LCP status (good/needs-improvement/poor)."""
        if lcp == 0:
            return "unknown"
        if lcp <= 2500:
            return "good"
        if lcp <= 4000:
            return "needs-improvement"
        return "poor"

    def _get_inp_status(self, inp: float) -> str:
        """Get INP status."""
        if inp == 0:
            return "unknown"
        if inp <= 200:
            return "good"
        if inp <= 500:
            return "needs-improvement"
        return "poor"

    def _get_cls_status(self, cls: float) -> str:
        """Get CLS status."""
        if cls == 0:
            return "unknown"
        if cls <= 0.1:
            return "good"
        if cls <= 0.25:
            return "needs-improvement"
        return "poor"

    def _get_script(self) -> str:
        """Get JavaScript for collecting Web Vitals."""
        return """() => {
            const result = {};

            // LCP - Largest Contentful Paint
            try {
                const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                if (lcpEntries.length > 0) {
                    const lastEntry = lcpEntries[lcpEntries.length - 1];
                    result.lcp = Math.round(lastEntry.renderTime || lastEntry.loadTime);
                } else {
                    // Fallback: estimate LCP from FCP + some buffer
                    const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
                    if (fcpEntry) {
                        result.lcp = Math.round(fcpEntry.startTime + 500); // Estimate
                    }
                }
            } catch (e) {}

            // INP - Interaction to Next Paint (complex calculation)
            try {
                const eventEntries = performance.getEntriesByType('event');
                if (eventEntries.length > 0) {
                    // Get interaction events only
                    const interactions = eventEntries.filter(e =>
                        e.cancelable &&
                        ['click', 'keydown', 'keyup', 'pointerdown', 'pointerup'].includes(e.name)
                    );

                    if (interactions.length > 0) {
                        // Calculate processing time for each interaction
                        const processingTimes = interactions.map(e => e.duration);
                        // INP is typically the 98th percentile or worst interaction
                        processingTimes.sort((a, b) => b - a);
                        result.inp = Math.round(processingTimes[0] || 0);
                    } else {
                        // Fallback: estimate INP from FID
                        const fidEntries = performance.getEntriesByType('first-input');
                        if (fidEntries.length > 0) {
                            result.inp = Math.round(fidEntries[0].processingStart - fidEntries[0].startTime);
                        }
                    }
                }
            } catch (e) {}

            // FID - First Input Delay (legacy, but still collected)
            try {
                const fidEntries = performance.getEntriesByType('first-input');
                if (fidEntries.length > 0) {
                    result.fid = Math.round(fidEntries[0].processingStart - fidEntries[0].startTime);
                }
            } catch (e) {}

            // CLS - Cumulative Layout Shift
            try {
                const clsEntries = performance.getEntriesByType('layout-shift');
                let cls = 0;
                clsEntries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        cls += entry.value;
                    }
                });
                result.cls = cls;
            } catch (e) {}

            // FCP - First Contentful Paint
            try {
                const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
                if (fcpEntry) {
                    result.fcp = Math.round(fcpEntry.startTime);
                }
            } catch (e) {}

            // TTI - Time to Interactive (approximation using domInteractive)
            try {
                const navEntry = performance.getEntriesByType('navigation')[0];
                if (navEntry) {
                    result.tti = Math.round(navEntry.domInteractive);
                }
            } catch (e) {}

            // TBT - Total Blocking Time (sum of long tasks)
            try {
                const longTasks = performance.getEntriesByType('longtask');
                let tbt = 0;
                longTasks.forEach(task => {
                    if (task.duration > 50) {
                        tbt += task.duration - 50;
                    }
                });
                result.tbt = Math.round(tbt);
            } catch (e) {}

            return result;
        }"""

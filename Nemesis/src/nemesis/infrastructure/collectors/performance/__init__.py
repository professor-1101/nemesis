"""
Performance metrics collection package.

Comprehensive performance monitoring for Chrome/Chromium with support for:
- Core Web Vitals (LCP, INP, CLS)
- Navigation & Resource Timing
- Paint Timing
- Memory metrics
- Long Tasks & Layout Shifts
- User Timing & Event Timing
- Runtime metrics

Usage:
    from nemesis.infrastructure.collectors.performance import PerformanceCollector

    collector = PerformanceCollector(page)
    report = collector.collect_all()
    collector.save_to_file(execution_id)
"""
from .performance_collector import PerformanceCollector
from .models import (
    PerformanceReport,
    NavigationTiming,
    ResourceTiming,
    PaintTiming,
    WebVitals,
    MemoryMetrics,
    RuntimeMetrics,
    LongTask,
    LayoutShift,
    UserTimingEntry,
    EventTiming,
)

__all__ = [
    'PerformanceCollector',
    'PerformanceReport',
    'NavigationTiming',
    'ResourceTiming',
    'PaintTiming',
    'WebVitals',
    'MemoryMetrics',
    'RuntimeMetrics',
    'LongTask',
    'LayoutShift',
    'UserTimingEntry',
    'EventTiming',
]

"""Main performance metrics collector with clean architecture."""
import traceback
from pathlib import Path
from typing import Dict, Any, List

from playwright.sync_api import Page

from nemesis.domain.ports import ICollector
from nemesis.shared.exceptions import CollectorError
from nemesis.infrastructure.logging import Logger
from nemesis.utils import get_path_manager

from .metric_collectors import (
    NavigationTimingCollector,
    ResourceTimingCollector,
    PaintTimingCollector,
    WebVitalsCollector,
    MemoryCollector,
    RuntimeMetricsCollector,
    LongTasksCollector,
    LayoutShiftsCollector,
    UserTimingCollector,
    EventTimingCollector,
)
from .models import PerformanceReport
from .exporters import JSONExporter


class PerformanceCollector(ICollector):
    """
    Comprehensive performance metrics collector for Chrome/Chromium browsers.

    Collects all major performance metrics including:
    - Core Web Vitals (LCP, INP, CLS)
    - Navigation & Resource Timing
    - Paint Timing (FP, FCP)
    - Memory metrics
    - Long Tasks & Layout Shifts
    - User Timing marks/measures
    - Event Timing (interactions)
    - Runtime metrics (FPS, frames)
    """

    def __init__(self, page: Page, capture_metrics: bool = True) -> None:
        """
        Initialize performance collector.

        :param page: Playwright page object
        :param capture_metrics: Enable or disable metrics collection
        """
        self.page = page
        self.capture_metrics = capture_metrics
        self.logger = Logger.get_instance({})

        # Initialize sub-collectors
        self._init_collectors()

    def _init_collectors(self) -> None:
        """Initialize all metric collectors."""
        if not self.capture_metrics:
            return

        self.navigation_collector = NavigationTimingCollector(self.page, self.logger)
        self.resource_collector = ResourceTimingCollector(self.page, self.logger)
        self.paint_collector = PaintTimingCollector(self.page, self.logger)
        self.web_vitals_collector = WebVitalsCollector(self.page, self.logger)
        self.memory_collector = MemoryCollector(self.page, self.logger)
        self.runtime_collector = RuntimeMetricsCollector(self.page, self.logger)
        self.longtask_collector = LongTasksCollector(self.page, self.logger)
        self.layout_shift_collector = LayoutShiftsCollector(self.page, self.logger)
        self.user_timing_collector = UserTimingCollector(self.page, self.logger)
        self.event_timing_collector = EventTimingCollector(self.page, self.logger)

    def collect_all(self) -> PerformanceReport:
        """
        Collect all performance metrics.

        :return: Complete performance report
        """
        if not self.capture_metrics:
            return PerformanceReport()

        try:
            # Collect resources first
            resources = self.resource_collector.collect()

            # Calculate resource summary
            resource_summary = self.resource_collector.calculate_summary(resources)

            report = PerformanceReport(
                navigation=self.navigation_collector.collect(),
                resources=resources,
                paint=self.paint_collector.collect(),
                web_vitals=self.web_vitals_collector.collect(),
                memory=self.memory_collector.collect(),
                runtime=self.runtime_collector.collect(),
                long_tasks=self.longtask_collector.collect(),
                layout_shifts=self.layout_shift_collector.collect(),
                user_timing=self.user_timing_collector.collect(),
                event_timing=self.event_timing_collector.collect(),
                resource_summary=resource_summary,
            )

            self.logger.info("Performance metrics collected successfully")
            return report

        except (AttributeError, RuntimeError) as e:
            # Page.evaluate or metric collection errors
            self.logger.error(f"Failed to collect performance metrics: {e}", traceback=traceback.format_exc(), module=__name__, class_name="PerformanceCollector", method="collect_all")
            raise CollectorError("Performance collection failed", str(e)) from e
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise

    def save_to_file(
        self,
        execution_id: str,
        _scenario_name: str | None = None
    ) -> Path:
        """
        Save metrics to JSON file.

        :param execution_id: Execution identifier
        :param scenario_name: Optional scenario name
        :return: Path to saved file
        """
        if not self.capture_metrics:
            return Path()

        try:
            report = self.collect_all()

            # Get save path
            file_path = self._get_save_path(execution_id)

            # Export to JSON
            exporter = JSONExporter()
            exporter.export(report, file_path)

            self.logger.info(f"Performance metrics saved: {file_path}")
            return file_path

        except (OSError, IOError, PermissionError) as e:
            # File system errors
            self.logger.error(f"Failed to save performance metrics - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="PerformanceCollector", method="save_to_file", execution_id=execution_id)
            raise CollectorError("Failed to save performance metrics", str(e)) from e
        except (AttributeError, RuntimeError) as e:
            # Export or collection errors
            self.logger.error(f"Failed to save performance metrics - export error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="PerformanceCollector", method="save_to_file", execution_id=execution_id)
            raise CollectorError("Failed to save performance metrics", str(e)) from e
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise

    def _get_save_path(self, execution_id: str) -> Path:
        """Get file path for saving metrics."""
        try:
            path_manager = get_path_manager()
            return path_manager.get_attachment_path(
                execution_id,
                "performance",
                "performance_metrics.json"
            )
        except (AttributeError, KeyError, RuntimeError) as e:
            # PathHelper initialization errors - fallback
            self.logger.debug(f"PathHelper failed, using fallback path: {e}", traceback=traceback.format_exc(), module=__name__, class_name="PerformanceCollector", method="_get_save_path", execution_id=execution_id)
            file_path = Path(f"reports/{execution_id}/performance/performance_metrics.json")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            return file_path
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise

    # ICollector interface implementation
    def start(self) -> None:
        """Start collecting performance metrics (collectors are initialized in __init__)."""
        if not self.capture_metrics:
            self._init_collectors()
            self.capture_metrics = True

    def stop(self) -> None:
        """Stop collecting performance metrics."""
        self.capture_metrics = False

    def get_collected_data(self) -> List[Dict[str, Any]]:
        """Get collected performance metrics as list."""
        if not self.capture_metrics:
            return []
        report = self.collect_all()
        return [report.to_dict()]

    def save_collected_data(
        self,
        execution_id: str,
        output_dir: Path,
        scenario_name: str = ""
    ) -> Path:
        """Save collected data to file."""
        return self.save_to_file(execution_id, scenario_name)

    def clear(self) -> None:
        """Clear collected data (reinitialize collectors)."""
        if self.capture_metrics:
            self._init_collectors()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.capture_metrics:
            return {}
        report = self.collect_all()
        return {
            "navigation": report.navigation.to_dict() if report.navigation else {},
            "web_vitals": report.web_vitals.to_dict() if report.web_vitals else {},
            "memory": report.memory.to_dict() if report.memory else {},
            "resource_summary": report.resource_summary or {},
        }

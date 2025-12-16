"""Allure metrics handling."""
import json
from pathlib import Path
from typing import Any, Optional

from nemesis.reporting.local.data_model import ScenarioData


class AllureMetricsBuilder:
    """Builds Allure metrics from performance data."""

    def __init__(self, results_dir: Path, execution_path: Path):
        """Initialize metrics builder.
        
        Args:
            results_dir: Directory where Allure results will be saved
            execution_path: Execution directory path (for finding performance data)
        """
        self.results_dir = results_dir
        self.execution_path = execution_path

    def build_metrics(self, scenario: ScenarioData) -> Optional[dict[str, Any]]:
        """Build Allure metrics from performance data.
        
        Args:
            scenario: Scenario data
            
        Returns:
            Metrics dictionary or None
        """
        metrics = {}
        
        # Load performance metrics from file
        performance_file = self.execution_path / "performance" / "performance_metrics.json"
        if performance_file.exists():
            try:
                with open(performance_file, 'r', encoding='utf-8') as f:
                    perf_data = json.load(f)
                
                # Extract Web Vitals and other metrics (support both web_vitals and webVitals)
                vitals = perf_data.get("web_vitals") or perf_data.get("webVitals")
                if vitals:
                    if "lcp" in vitals:
                        metrics["largestContentfulPaint"] = vitals["lcp"]
                    if "fid" in vitals:
                        metrics["firstInputDelay"] = vitals["fid"]
                    if "cls" in vitals:
                        metrics["cumulativeLayoutShift"] = vitals["cls"]
                    if "fcp" in vitals:
                        metrics["firstContentfulPaint"] = vitals["fcp"]
                    # TTFB might be in navigation, not web_vitals
                    if "ttfb" in vitals:
                        metrics["timeToFirstByte"] = vitals["ttfb"]
                
                # Extract paint metrics
                if "paint" in perf_data:
                    paint = perf_data["paint"]
                    if "first-paint" in paint:
                        metrics["firstPaint"] = paint["first-paint"]
                    if "first-contentful-paint" in paint:
                        # Avoid duplicate if already set from webVitals
                        if "firstContentfulPaint" not in metrics:
                            metrics["firstContentfulPaint"] = paint["first-contentful-paint"]
                
                # Extract navigation timing
                if "navigation" in perf_data:
                    nav = perf_data["navigation"]
                    if "dom_content_loaded_end" in nav:
                        metrics["domContentLoaded"] = nav["dom_content_loaded_end"]
                    elif "domContentLoaded" in nav:
                        metrics["domContentLoaded"] = nav["domContentLoaded"]
                    if "load_event_end" in nav:
                        metrics["pageLoad"] = nav["load_event_end"]
                    elif "load" in nav:
                        metrics["pageLoad"] = nav["load"]
                    if "dom_interactive" in nav:
                        metrics["domInteractive"] = nav["dom_interactive"]
                    elif "domInteractive" in nav:
                        metrics["domInteractive"] = nav["domInteractive"]
                    # TTFB from navigation if not in web_vitals
                    if "ttfb" in nav and "timeToFirstByte" not in metrics:
                        metrics["timeToFirstByte"] = nav["ttfb"]
                
                # Extract memory metrics
                if "memory" in perf_data:
                    memory = perf_data["memory"]
                    if "used_js_heap_size" in memory:
                        metrics["usedJSHeapSize"] = memory["used_js_heap_size"]
                    elif "usedJSHeapSize" in memory:
                        metrics["usedJSHeapSize"] = memory["usedJSHeapSize"]
                    if "total_js_heap_size" in memory:
                        metrics["totalJSHeapSize"] = memory["total_js_heap_size"]
                    elif "totalJSHeapSize" in memory:
                        metrics["totalJSHeapSize"] = memory["totalJSHeapSize"]
                
            except (json.JSONDecodeError, IOError, KeyError):
                pass
        
        return metrics if metrics else None
    
    def save_metrics_file(self, test_uuid: str, metrics: dict[str, Any]) -> None:
        """Save metrics to Allure metrics file.
        
        Allure expects metrics in a specific format:
        {
            "name": "metric_name",
            "value": numeric_value,
            "type": "timer" | "gauge" | "counter"
        }
        
        Args:
            test_uuid: Test UUID
            metrics: Metrics dictionary (will be converted to Allure format)
        """
        try:
            # Convert metrics to Allure format
            allure_metrics = []
            for name, value in metrics.items():
                if isinstance(value, (int, float)):
                    # Allure metrics format
                    metric_entry = {
                        "name": name,
                        "value": value,
                        "type": "timer" if "time" in name.lower() or "delay" in name.lower() or "paint" in name.lower() or "load" in name.lower() else "gauge"
                    }
                    allure_metrics.append(metric_entry)
            
            if allure_metrics:
                metrics_file = self.results_dir / f"{test_uuid}-metrics.json"
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(allure_metrics, f, indent=2, ensure_ascii=False)
        except (OSError, IOError, TypeError):
            pass


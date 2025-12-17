"""JSON Reporter - Simple JSON output implementation

This reporter generates structured JSON reports.
Framework does NOT generate HTML - that's test project responsibility.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.ports import IReporter
from nemesis.infrastructure.logging import Logger


class JSONReporter(IReporter):
    """
    Adapter: JSON Reporter

    Implements IReporter to generate simple JSON reports.

    Design Decision: Framework generates JSON ONLY, not HTML.
    - Test projects can visualize JSON however they want
    - Separation of concerns
    - Framework independence

    Clean Architecture:
    - Implements Domain port (IReporter)
    - Infrastructure layer adapter
    """

    def __init__(self, output_dir: Path):
        """
        Initialize reporter

        Args:
            output_dir: Directory to save JSON reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._current_execution: Optional[Execution] = None

    def start_execution(self, execution: Execution) -> None:
        """Report execution start"""
        self._current_execution = execution
        Logger.get_instance({}).info(f"[JSONReporter] Started execution: {execution.execution_id}")

    def end_execution(self, execution: Execution) -> None:
        """Report execution end"""
        Logger.get_instance({}).info(f"[JSONReporter] Ended execution: {execution.execution_id}")
        Logger.get_instance({}).info(f"  Scenarios: {execution.get_total_scenarios_count()}")
        Logger.get_instance({}).info(f"  Passed: {execution.get_passed_scenarios_count()}")
        Logger.get_instance({}).info(f"  Failed: {execution.get_failed_scenarios_count()}")

    def start_scenario(self, scenario: Scenario) -> None:
        """Report scenario start"""
        Logger.get_instance({}).info(f"[JSONReporter] Started scenario: {scenario.name}")

    def end_scenario(self, scenario: Scenario) -> None:
        """Report scenario end"""
        status_icon = "✓" if scenario.is_successful() else "✗"
        Logger.get_instance({}).info(f"[JSONReporter] {status_icon} {scenario.name} - {scenario.status}")

    def start_step(self, step: Step) -> None:
        """Report step start"""
        pass  # Silent for steps to avoid clutter

    def end_step(self, step: Step) -> None:
        """Report step end"""
        pass  # Silent for steps

    def attach_file(
        self,
        file_path: Path,
        description: str = "",
        attachment_type: str = ""
    ) -> None:
        """Attach file (logged but not processed by JSON reporter)"""
        pass

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message"""
        pass

    def generate_report(self, execution: Execution, output_dir: Path) -> Optional[Path]:
        """
        Generate JSON report

        Args:
            execution: Execution entity with all data
            output_dir: Directory to save report

        Returns:
            Path to generated JSON file
        """
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate report filename
        report_filename = f"execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = output_dir / report_filename

        # Convert execution to dictionary
        report_data = execution.to_dict()

        # Write JSON file with pretty printing
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        Logger.get_instance({}).info(f"\n[JSONReporter] Report generated: {report_path}")
        return report_path

"""Generate Execution Report Use Case

This use case generates the final execution report after all tests complete.
"""

from typing import List
from pathlib import Path

from nemesis.domain.entities import Execution
from nemesis.domain.ports import IReporter


class GenerateExecutionReportUseCase:
    """
    Use Case: Generate Execution Report

    Responsibilities:
    - Coordinate report generation across multiple reporters
    - Ensure all reporters complete successfully
    - Return report paths for user access

    Clean Architecture:
    - Depends on Domain (Execution)
    - Depends on Ports (IReporter), not implementations
    """

    def __init__(self, reporters: List[IReporter]):
        """
        Initialize with reporters

        Args:
            reporters: List of reporter implementations
        """
        self.reporters = reporters

    def execute(self, execution: Execution, output_dir: Path) -> List[Path]:
        """
        Generate reports for execution

        Args:
            execution: Execution entity with all results
            output_dir: Directory to save reports

        Returns:
            List of paths to generated reports
        """
        report_paths = []

        # Generate report with each reporter
        for reporter in self.reporters:
            try:
                report_path = reporter.generate_report(execution, output_dir)
                if report_path:
                    report_paths.append(report_path)
            except Exception as e:
                # Log but don't fail entire reporting
                print(f"Warning: Reporter {reporter.__class__.__name__} failed: {e}")

        return report_paths

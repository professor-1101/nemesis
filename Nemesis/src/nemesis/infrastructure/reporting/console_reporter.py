"""Console Reporter - Cypress-like CLI output

This reporter provides beautiful console output similar to Cypress.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import StepStatus
from nemesis.domain.ports import IReporter


class ConsoleReporter(IReporter):
    """
    Adapter: Console Reporter (Cypress-style)

    Provides beautiful CLI output similar to Cypress test runner.

    Features:
    - Progress indicators
    - Color-coded output (green/red)
    - Summary statistics
    - Duration tracking

    Clean Architecture:
    - Implements IReporter interface
    - Infrastructure layer adapter
    """

    # ANSI Color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self):
        """Initialize console reporter"""
        self._current_execution: Optional[Execution] = None
        self._current_scenario: Optional[Scenario] = None
        self._feature_index = 0
        self._total_features = 0

    def start_execution(self, execution: Execution) -> None:
        """Report execution start"""
        self._current_execution = execution

        print(f"\n{self.CYAN}{self.BOLD}NEMESIS Test Automation Framework{self.RESET}")
        print(f"{self.CYAN}─────────────────────────────────────{self.RESET}\n")

    def end_execution(self, execution: Execution) -> None:
        """Report execution end with summary"""
        self._current_execution = execution

        # Summary
        total = execution.get_total_scenarios_count()
        passed = execution.get_passed_scenarios_count()
        failed = execution.get_failed_scenarios_count()
        skipped = execution.get_skipped_scenarios_count()
        duration = execution.get_duration()

        print(f"\n{self.CYAN}─────────────────────────────────────{self.RESET}")

        # Passed scenarios
        if passed > 0:
            print(f"  {self.GREEN}{passed} passing{self.RESET} ({duration})")

        # Failed scenarios
        if failed > 0:
            print(f"  {self.RED}{failed} failing{self.RESET}")

        # Skipped scenarios
        if skipped > 0:
            print(f"  {self.YELLOW}{skipped} skipped{self.RESET}")

        print(f"{self.CYAN}─────────────────────────────────────{self.RESET}\n")

    def start_scenario(self, scenario: Scenario) -> None:
        """Report scenario start (Cypress-style)"""
        self._current_scenario = scenario

        # Print feature header if first scenario of feature
        if not hasattr(self, '_current_feature') or self._current_feature != scenario.feature_name:
            self._current_feature = scenario.feature_name
            print(f"\n  {self.CYAN}{scenario.feature_name}{self.RESET}")

    def end_scenario(self, scenario: Scenario) -> None:
        """Report scenario end (Cypress-style)"""
        # Status icon
        if scenario.is_successful():
            icon = f"{self.GREEN}✓{self.RESET}"
            color = self.GREEN
        elif scenario.is_failed():
            icon = f"{self.RED}✗{self.RESET}"
            color = self.RED
        else:
            icon = f"{self.YELLOW}-{self.RESET}"
            color = self.YELLOW

        # Duration
        duration = scenario.get_duration()

        # Print scenario result
        print(f"    {icon} {scenario.name} {self.RESET}({duration}){self.RESET}")

        # Print failed step details
        if scenario.is_failed():
            for step in scenario.steps:
                if step.is_failed():
                    print(f"      {self.RED}{step.error_message}{self.RESET}")

    def start_step(self, step: Step) -> None:
        """Report step start (silent)"""
        pass

    def end_step(self, step: Step) -> None:
        """Report step end (silent unless failed)"""
        pass

    def attach_file(
        self,
        file_path: Path,
        description: str = "",
        attachment_type: str = ""
    ) -> None:
        """Attach file (silent in console)"""
        pass

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message"""
        if level == "ERROR":
            print(f"  {self.RED}[ERROR] {message}{self.RESET}")
        elif level == "WARNING":
            print(f"  {self.YELLOW}[WARN] {message}{self.RESET}")
        else:
            print(f"  [INFO] {message}")

    def generate_report(self, execution: Execution, output_dir: Path) -> Optional[Path]:
        """Console reporter doesn't generate files"""
        return None

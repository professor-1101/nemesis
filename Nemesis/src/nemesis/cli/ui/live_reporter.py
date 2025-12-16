"""Real-time test execution reporter with live progress display"""

from typing import Optional, List
from datetime import datetime, timedelta
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.tree import Tree

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import ScenarioStatus, StepStatus
from nemesis.domain.ports import IReporter


class LiveReporter(IReporter):
    """IReporter implementation with real-time terminal UI updates"""

    def __init__(self, console: Optional[Console] = None):
        """Initialize live reporter"""
        self.console = console or Console()
        self.live: Optional[Live] = None

        # State tracking
        self.execution: Optional[Execution] = None
        self.current_scenario: Optional[Scenario] = None
        self.current_step: Optional[Step] = None

        # Statistics
        self.total_scenarios = 0
        self.completed_scenarios = 0
        self.passed_scenarios = 0
        self.failed_scenarios = 0
        self.skipped_scenarios = 0

        self.total_steps = 0
        self.passed_steps = 0
        self.failed_steps = 0

        # Timing
        self.start_time: Optional[datetime] = None

        # Display components
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        )
        self.scenario_task_id: Optional[int] = None

    def start_execution(self, execution: Execution) -> None:
        """Start execution and begin live display"""
        self.execution = execution
        self.start_time = datetime.now()

        # Start live display
        self.live = Live(
            self._render_display(),
            console=self.console,
            refresh_per_second=4,
            vertical_overflow="visible",
        )
        self.live.start()

    def end_execution(self, execution: Execution) -> None:
        """End execution and show final summary"""
        self.execution = execution

        if self.live:
            # Final update
            self.live.update(self._render_display())
            self.live.stop()

        # Show final summary
        self._show_final_summary()

    def start_scenario(self, scenario: Scenario) -> None:
        """Start scenario execution"""
        self.current_scenario = scenario
        self.total_scenarios += 1

        # Update display
        if self.live:
            self.live.update(self._render_display())

    def end_scenario(self, scenario: Scenario) -> None:
        """End scenario execution"""
        self.completed_scenarios += 1

        # Update statistics
        if scenario.status == ScenarioStatus.PASSED:
            self.passed_scenarios += 1
        elif scenario.status == ScenarioStatus.FAILED:
            self.failed_scenarios += 1
        elif scenario.status == ScenarioStatus.SKIPPED:
            self.skipped_scenarios += 1

        # Update display
        if self.live:
            self.live.update(self._render_display())

        self.current_scenario = None

    def start_step(self, step: Step) -> None:
        """Start step execution"""
        self.current_step = step
        self.total_steps += 1

        # Update display
        if self.live:
            self.live.update(self._render_display())

    def end_step(self, step: Step) -> None:
        """End step execution"""
        # Update statistics
        if step.status == StepStatus.PASSED:
            self.passed_steps += 1
        elif step.status == StepStatus.FAILED:
            self.failed_steps += 1

        # Update display
        if self.live:
            self.live.update(self._render_display())

        self.current_step = None

    def attach_file(self, file_path, description: str = "", attachment_type: str = "") -> None:
        """Attach file (screenshots, videos, etc.)"""
        # Could show file attachments in the display
        pass

    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log message"""
        # Could show log messages in the display
        pass

    def generate_report(self, execution: Execution, output_dir) -> Optional:
        """Generate report (no-op for live reporter)"""
        return None

    def _render_display(self) -> Group:
        """Render the complete live display"""
        components = []

        # 1. Header
        components.append(self._render_header())

        # 2. Current scenario
        if self.current_scenario:
            components.append(self._render_current_scenario())

        # 3. Statistics
        components.append(self._render_statistics())

        return Group(*components)

    def _render_header(self) -> Panel:
        """Render header panel"""
        if not self.execution:
            return Panel("Initializing...", style="bold blue")

        # Calculate progress
        progress_percent = 0
        if self.total_scenarios > 0:
            progress_percent = int((self.completed_scenarios / self.total_scenarios) * 100)

        # Calculate elapsed time
        elapsed = ""
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
            elapsed = f"{int(elapsed_seconds)}s"

        header_text = (
            f"[bold]Running Tests[/bold]\n\n"
            f"Execution: {self.execution.execution_id}\n"
            f"Progress: {self.completed_scenarios}/{self.total_scenarios} scenarios ({progress_percent}%)\n"
            f"Elapsed: {elapsed}"
        )

        return Panel(header_text, style="bold cyan", border_style="cyan")

    def _render_current_scenario(self) -> Panel:
        """Render current scenario being executed"""
        if not self.current_scenario:
            return Panel("No active scenario", style="dim")

        # Scenario header
        scenario_status = self._get_status_icon(self.current_scenario.status.value)
        scenario_name = self.current_scenario.name
        feature_name = self.current_scenario.feature_name

        content = [
            f"[bold]{scenario_status} {feature_name}: {scenario_name}[/bold]\n"
        ]

        # Show steps
        for step in self.current_scenario.steps:
            step_status = self._get_status_icon(step.status.value)
            step_name = f"{step.keyword} {step.name}"

            # Duration if completed
            duration_str = ""
            if step.is_completed():
                duration = step.get_duration()
                duration_str = f" [dim]({duration.format_short()})[/dim]"

            # Current step indicator
            is_current = step == self.current_step
            if is_current:
                content.append(f"  [bold cyan]→ {step_status} {step_name}[/bold cyan]{duration_str}")
            else:
                content.append(f"    {step_status} {step_name}{duration_str}")

            # Show error if failed
            if step.status == StepStatus.FAILED and step.error_message:
                content.append(f"      [red]└─ {step.error_message}[/red]")

        return Panel("\n".join(content), style="white", border_style="blue")

    def _render_statistics(self) -> Table:
        """Render statistics table"""
        table = Table(show_header=False, box=None, padding=(0, 2))

        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        # Scenarios
        table.add_row(
            "✓ Passing",
            f"[green]{self.passed_scenarios}[/green]"
        )
        table.add_row(
            "✗ Failing",
            f"[red]{self.failed_scenarios}[/red]"
        )
        table.add_row(
            "○ Skipped",
            f"[yellow]{self.skipped_scenarios}[/yellow]"
        )

        # Steps
        table.add_row("", "")  # Spacer
        table.add_row(
            "Steps Passed",
            f"[green]{self.passed_steps}[/green]"
        )
        table.add_row(
            "Steps Failed",
            f"[red]{self.failed_steps}[/red]"
        )

        return Panel(table, title="Test Results", style="white", border_style="green")

    def _show_final_summary(self) -> None:
        """Show final summary after execution"""
        if not self.execution:
            return

        self.console.print()
        self.console.rule("[bold]Test Execution Complete[/bold]", style="green")
        self.console.print()

        # Results table
        table = Table(title="Final Results", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="white")
        table.add_column("Percentage", justify="right", style="yellow")

        total = self.total_scenarios
        if total > 0:
            pass_pct = int((self.passed_scenarios / total) * 100)
            fail_pct = int((self.failed_scenarios / total) * 100)
            skip_pct = int((self.skipped_scenarios / total) * 100)
        else:
            pass_pct = fail_pct = skip_pct = 0

        table.add_row("✓ Passed", str(self.passed_scenarios), f"{pass_pct}%")
        table.add_row("✗ Failed", str(self.failed_scenarios), f"{fail_pct}%")
        table.add_row("○ Skipped", str(self.skipped_scenarios), f"{skip_pct}%")
        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "100%")

        self.console.print(table)
        self.console.print()

        # Duration
        if self.start_time:
            duration = datetime.now() - self.start_time
            self.console.print(f"[bold]Duration:[/bold] {duration.total_seconds():.1f}s")

        # Exit status
        if self.failed_scenarios == 0:
            self.console.print("\n[bold green]✓ All tests passed![/bold green]\n")
        else:
            self.console.print(f"\n[bold red]✗ {self.failed_scenarios} test(s) failed[/bold red]\n")

    @staticmethod
    def _get_status_icon(status: str) -> str:
        """Get icon for status"""
        icons = {
            "PENDING": "○",
            "RUNNING": "●",
            "PASSED": "✓",
            "FAILED": "✗",
            "SKIPPED": "○",
            "UNDEFINED": "?",
        }
        return icons.get(status.upper(), "?")

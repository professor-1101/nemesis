"""Rich table displays for CLI."""
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


console = Console()


def show_configuration_table(
        env: str,
        report: str,
        headless: bool,
        debug: bool,
        parallel: int,
        tags: tuple,
        feature: Optional[str],
) -> None:
    """Display test configuration table."""
    table = Table(
        title="[bold cyan]Configuration[/bold cyan]",
        show_header=False,
        border_style="cyan",
        padding=(0, 2),
    )

    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="bright_white")

    table.add_row("Environment", env)
    table.add_row("Report Mode", report)
    table.add_row("Browser", "Headless" if headless else "Headed")
    table.add_row("Debug", "Enabled" if debug else "Disabled")

    if parallel > 1:
        table.add_row("Parallel Workers", str(parallel))

    if tags:
        table.add_row("Tags", ", ".join(tags))

    if feature:
        table.add_row("Feature", feature)

    console.print(table)


def show_execution_summary(env: str, report: str, exit_code: int) -> None:
    """Display execution summary."""
    table = Table(
        title="[bold cyan]Summary[/bold cyan]",
        show_header=False,
        border_style="cyan",
        padding=(0, 2),
    )

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="bright_white")

    status = "Passed" if exit_code == 0 else "Failed"
    status_color = "green" if exit_code == 0 else "red"

    table.add_row("Environment", env)
    table.add_row("Report Mode", report)
    table.add_row("Status", f"[{status_color}]{status}[/{status_color}]")

    console.print(table)


def show_executions_table(executions: List[Dict[str, Any]]) -> None:
    """Display test executions table."""
    table = Table(
        title="[bold cyan]Test Executions[/bold cyan]",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
        padding=(0, 1),
    )

    table.add_column("ID", style="cyan", no_wrap=True, width=20)
    table.add_column("Date", style="blue", width=12)
    table.add_column("Time", style="blue", width=10)
    table.add_column("Status", style="bold", width=10)
    table.add_column("Size", style="dim", justify="right", width=10)

    for execution in executions:
        status = execution.get("status", "unknown")

        if status == "passed":
            status_text = "[green]✓ Passed[/green]"
        elif status == "failed":
            status_text = "[red]✗ Failed[/red]"
        else:
            status_text = "[yellow]? Unknown[/yellow]"

        size_bytes = execution.get("size", 0)
        size_str = _format_size(size_bytes)

        table.add_row(
            execution.get("id", "N/A"),
            execution.get("date", "N/A"),
            execution.get("time", "N/A"),
            status_text,
            size_str,
        )

    console.print(table)


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f}TB"

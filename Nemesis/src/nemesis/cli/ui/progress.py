"""Progress indicators and spinners."""
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

console = Console()


def show_execution_progress(_total_steps: int = 100):
    """Create execution progress bar.

    Args:
        _total_steps: Total number of steps (unused, kept for API compatibility)

    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[cyan]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
        TimeElapsedColumn(),
        console=console,
    )

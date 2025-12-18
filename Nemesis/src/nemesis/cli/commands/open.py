"""CLI open command - Show JSON report path."""
import json
import sys
import traceback
from pathlib import Path

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

from nemesis.infrastructure.logging import Logger
from ..ascii_art import print_error, print_step, print_success
from ..core.report_scanner import ReportScanner

console = Console()
LOGGER = Logger.get_instance({})


@click.command()
@click.argument("execution_id", required=False)
@click.option(
    "--latest",
    "-l",
    is_flag=True,
    help="Show the latest execution report",
)
def open_command(execution_id: str | None, latest: bool) -> None:
    """Show JSON execution report.

    \b
    Examples:
      nemesis open --latest              Show latest report
      nemesis open <execution-id>        Show specific execution report
      nemesis open                       Show latest report (if no ID provided)
    """
    try:
        console.print()
        print_step("Finding JSON report...")
        console.print()

        # Find report directory
        scanner = ReportScanner()
        reports_path = scanner.get_reports_path()

        if not reports_path or not reports_path.exists():
            console.print("[yellow]⚠ No reports directory found[/yellow]")
            console.print("[dim]Run tests first: [bold]nemesis run[/bold][/dim]\n")
            return

        # Determine which execution to show
        target_execution_id = None
        if latest:
            executions = scanner.scan_reports(limit=1, sort_by="date")
            if executions:
                target_execution_id = executions[0].get("execution_id")
            else:
                console.print("[yellow]⚠ No executions found[/yellow]\n")
                return
        elif execution_id:
            target_execution_id = execution_id
        else:
            # Default to latest if no ID provided
            executions = scanner.scan_reports(limit=1, sort_by="date")
            if executions:
                target_execution_id = executions[0].get("execution_id")
            else:
                console.print("[yellow]⚠ No executions found[/yellow]\n")
                return

        if not target_execution_id:
            console.print("[yellow]⚠ Execution ID not found[/yellow]\n")
            return

        # Find execution directory
        execution_dir = reports_path / target_execution_id
        if not execution_dir.exists():
            console.print(f"[yellow]⚠ Execution directory not found: {target_execution_id}[/yellow]\n")
            return

        # Check for JSON report
        json_report = execution_dir / "reports" / "execution.json"
        if not json_report.exists():
            console.print("[yellow]⚠ JSON report not found[/yellow]")
            console.print(f"[dim]Report file: {json_report}[/dim]")
            console.print("[dim]Run tests first to generate report[/dim]\n")
            return

        # Show JSON report
        print_step(f"Showing report: {target_execution_id}")
        console.print()

        with open(json_report, 'r') as f:
            report_data = json.load(f)

        console.print(Panel(JSON(json.dumps(report_data, indent=2)),
                           title=f"[bold cyan]Execution Report[/bold cyan]",
                           border_style="cyan"))
        print_success(f"\nReport path: {json_report}")
        console.print()

    except SystemExit:  # pylint: disable=try-except-raise
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Open command interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError) as e:
        LOGGER.error(f"Failed to show report - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="open_command")
        print_error(f"Failed to show report - I/O error: {e}")
        sys.exit(1)
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        LOGGER.error(f"Failed to show report - Invalid input: {e}", traceback=traceback.format_exc(), module=__name__, function="open_command")
        print_error(f"Failed to show report - Invalid input: {e}")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        LOGGER.error(f"Failed to show report: {e}", traceback=traceback.format_exc(), module=__name__, function="open_command")
        print_error(f"Failed to show report: {e}")
        sys.exit(1)


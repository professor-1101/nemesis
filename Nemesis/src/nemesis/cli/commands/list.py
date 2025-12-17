"""CLI list command - List test executions."""
import sys
import traceback

import click
from rich.console import Console

from nemesis.infrastructure.logging import Logger
from ..ascii_art import print_error, print_step
from ..core.report_scanner import ReportScanner
from ..ui.tables import show_executions_table

console = Console()
LOGGER = Logger.get_instance({})


@click.command()
@click.option("--limit", "-l", type=int, default=10, help="Number of executions to show")
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["date", "status", "duration"]),
    default="date",
    help="Sort by field",
)
@click.option(
    "--filter-status",
    type=click.Choice(["passed", "failed", "all"]),
    default="all",
    help="Filter by status",
)
def list_command(limit: int, sort: str, filter_status: str) -> None:
    """List recent test executions with details.

    \b
    Examples:
      nemesis list                        Show recent executions
      nemesis list --limit 20             Show more executions
      nemesis list --filter-status failed Show only failures
      nemesis list --sort duration        Sort by duration
    """
    try:
        console.print()
        print_step("Loading test executions...")
        console.print()

        scanner = ReportScanner()
        executions = scanner.scan_reports(limit=limit, sort_by=sort)

        if not executions:
            console.print("[yellow]⚠ No test executions found[/yellow]")
            console.print("[dim]Run tests first: [bold]nemesis run[/bold][/dim]\n")
            return

        # Apply status filter
        if filter_status != "all":
            executions = [e for e in executions if e.get("status") == filter_status]

        if not executions:
            console.print(f"[yellow]⚠ No {filter_status} executions found[/yellow]\n")
            return

        # Show table
        show_executions_table(executions)

        console.print(f"\n[dim]Showing {len(executions)} execution(s)[/dim]\n")

    except SystemExit:  # pylint: disable=try-except-raise
        # Re-raise SystemExit to allow proper program termination
        # NOTE: SystemExit must propagate to allow proper exit code handling
        LOGGER.debug("SystemExit caught in list_command, propagating", module=__name__, function="list_command")
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ List command interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError) as e:
        # File system errors during report scanning
        LOGGER.error(f"Failed to list executions - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="list_command")
        print_error(f"Failed to list executions - I/O error: {e}")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        # Invalid parameter errors
        LOGGER.error(f"Failed to list executions - Invalid input: {e}", traceback=traceback.format_exc(), module=__name__, function="list_command")
        print_error(f"Failed to list executions - Invalid input: {e}")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Rich library or other dependencies
        # NOTE: Rich library may raise various exceptions we cannot predict
        LOGGER.error(f"Failed to list executions: {e}", traceback=traceback.format_exc(), module=__name__, function="list_command")
        print_error(f"Failed to list executions: {e}")
        sys.exit(1)

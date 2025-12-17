"""CLI open command - Open Allure report in browser."""
import sys
import traceback
from pathlib import Path

import click
from rich.console import Console

from nemesis.infrastructure.logging import Logger
from nemesis.reporting.local.allure.allure_cli_manager import AllureCLIManager, AllureCLINotInstalledError
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
    help="Open the latest execution report",
)
def open_command(execution_id: str | None, latest: bool) -> None:
    """Open Allure report in browser.

    \b
    Examples:
      nemesis open --latest              Open latest report
      nemesis open <execution-id>        Open specific execution report
      nemesis open                       Open latest report (if no ID provided)
    """
    try:
        console.print()
        print_step("Finding Allure report...")
        console.print()

        # Find report directory
        scanner = ReportScanner()
        reports_path = scanner.get_reports_path()
        
        if not reports_path or not reports_path.exists():
            console.print("[yellow]⚠ No reports directory found[/yellow]")
            console.print("[dim]Run tests first: [bold]nemesis run[/bold][/dim]\n")
            return

        # Determine which execution to open
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

        # Check for Allure report
        allure_report_dir = execution_dir / "allure-report"
        if not allure_report_dir.exists():
            console.print("[yellow]⚠ Allure report not found[/yellow]")
            console.print(f"[dim]Report directory: {allure_report_dir}[/dim]")
            console.print("[dim]Run tests first to generate Allure report[/dim]\n")
            return

        # Open report using Allure CLI
        print_step(f"Opening Allure report: {target_execution_id}")
        console.print()

        try:
            cli_manager = AllureCLIManager()
            success, error_msg = cli_manager.open_report(allure_report_dir)

            if success:
                print_success("Allure report opened in browser")
                console.print(f"[dim]Report: {allure_report_dir}[/dim]\n")
            else:
                print_error(f"Failed to open report: {error_msg}")
                console.print("[dim]You can manually open it with: allure open <report-dir>[/dim]\n")
        except AllureCLINotInstalledError as e:
            print_error("Allure CLI is not installed")
            console.print(f"[dim]{e.message}[/dim]")
            console.print("[dim]Install from: https://adoptium.net/temurin/releases/[/dim]")
            console.print("[dim]Then install Allure CLI: npm install -g allure-commandline[/dim]\n")
            sys.exit(1)

    except SystemExit:  # pylint: disable=try-except-raise
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Open command interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError) as e:
        LOGGER.error(f"Failed to open report - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="open_command")
        print_error(f"Failed to open report - I/O error: {e}")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        LOGGER.error(f"Failed to open report - Invalid input: {e}", traceback=traceback.format_exc(), module=__name__, function="open_command")
        print_error(f"Failed to open report - Invalid input: {e}")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        LOGGER.error(f"Failed to open report: {e}", traceback=traceback.format_exc(), module=__name__, function="open_command")
        print_error(f"Failed to open report: {e}")
        sys.exit(1)


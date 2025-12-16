"""CLI clean command - Clean old reports."""
import sys
import traceback

import click
from rich.console import Console
from rich.prompt import Confirm

from nemesis.core.logging import Logger
from ..ascii_art import print_error, print_step, print_success
from ..core  import ReportCleaner

console = Console()
LOGGER = Logger.get_instance({})


@click.command()
@click.option("--older-than", "-o", default="7d", help="Delete reports older than (e.g., 7d, 24h, 30m)")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
def clean_command(older_than: str, force: bool, dry_run: bool) -> None:
    """Clean old test reports to free up disk space.

    \b
    Time Formats:
      7d   7 days
      24h  24 hours
      30m  30 minutes

    \b
    Examples:
      nemesis clean                        Clean reports older than 7 days
      nemesis clean --older-than 30d       Clean reports older than 30 days
      nemesis clean --older-than 7d -f     Clean without confirmation
      nemesis clean --dry-run              Preview what would be deleted
    """
    try:
        console.print()
        print_step(f"Scanning for reports older than {older_than}...")
        console.print()

        cleaner = ReportCleaner()
        old_reports = cleaner.find_old_reports(older_than)

        if not old_reports:
            console.print("[green]✓ No old reports to clean[/green]")
            console.print("[dim]All reports are recent[/dim]\n")
            return

        total_size = cleaner.calculate_total_size(old_reports)

        console.print(f"[yellow]Found {len(old_reports)} report(s) older than {older_than}[/yellow]")
        console.print(f"[dim]Total size: {total_size}[/dim]\n")

        if dry_run:
            console.print("[cyan]Dry run - Reports that would be deleted:[/cyan]\n")
            for report in old_reports:
                console.print(f"  [dim]• {report.name}[/dim]")
            console.print("\n[green]✓ Dry run complete[/green]\n")
            return

        # Confirm deletion
        if not force:
            confirmed = Confirm.ask(
                f"[yellow]Delete {len(old_reports)} report(s)?[/yellow]",
                default=False,
            )
            if not confirmed:
                console.print("[yellow]⚠ Cleanup cancelled[/yellow]\n")
                return

        # Delete reports
        print_step("Deleting reports...")
        deleted_count = cleaner.delete_reports(old_reports)

        console.print()
        print_success(f"Deleted {deleted_count} report(s)")
        console.print(f"[dim]Freed up {total_size}[/dim]\n")

    except SystemExit:  # pylint: disable=try-except-raise
        # Re-raise SystemExit to allow proper program termination
        # NOTE: SystemExit must propagate to allow proper exit code handling
        LOGGER.debug("SystemExit caught in clean_command, propagating", module=__name__, function="clean_command")
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Cleanup interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError) as e:
        # File system errors during cleanup
        LOGGER.error(f"Clean failed - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="clean_command")
        print_error(f"Clean failed - I/O error: {e}")
        sys.exit(1)
    except ValueError as e:
        # Invalid duration format or other value errors
        LOGGER.error(f"Clean failed - Invalid input: {e}", traceback=traceback.format_exc(), module=__name__, function="clean_command")
        print_error(f"Clean failed - Invalid input: {e}")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Rich library or other dependencies
        # NOTE: Rich library may raise various exceptions we cannot predict
        LOGGER.error(f"Clean failed: {e}", traceback=traceback.format_exc(), module=__name__, function="clean_command")
        print_error(f"Clean failed: {e}")
        sys.exit(1)

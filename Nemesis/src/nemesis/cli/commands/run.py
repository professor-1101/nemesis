"""CLI run command - Execute tests."""
import sys
import traceback
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions
from ..ascii_art  import print_banner, print_error, print_step, print_success
from ..core.executor import TestExecutor
from ..ui.tables import show_configuration_table, show_execution_summary

console = Console()
LOGGER = Logger.get_instance({})


def _get_latest_execution_id():
    """Get execution_id from the most recent report directory."""
    try:
        reports_dir = Path("reports")
        if not reports_dir.exists():
            return None

        # Get all execution directories (sorted by modification time)
        execution_dirs = [d for d in reports_dir.iterdir() if d.is_dir()]
        if not execution_dirs:
            return None

        # Get the most recent one
        latest_dir = max(execution_dirs, key=lambda d: d.stat().st_mtime)
        return latest_dir.name
    except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
        # Always re-raise these to allow proper program termination
        # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
        raise
    except (OSError, IOError) as e:
        # File system errors - silently return None
        LOGGER.debug(f"Error getting latest execution ID: {e}", traceback=traceback.format_exc(), module=__name__, function="_get_latest_execution_id")
        return None


@handle_exceptions(
    log_level="debug",
    catch_exceptions=(OSError, IOError, ValueError, AttributeError, Exception),
    message_template="Failed to show report path: {error}"
)
def _show_report_path():
    """Show JSON report path if it exists."""
    # Find the most recent report directory
    reports_dir = Path("reports")
    if not reports_dir.exists():
        return

    # Get all execution directories (sorted by modification time)
    execution_dirs = [d for d in reports_dir.iterdir() if d.is_dir()]
    if not execution_dirs:
        return

    # Get the most recent one
    latest_dir = max(execution_dirs, key=lambda d: d.stat().st_mtime)
    json_report = latest_dir / "reports" / "execution.json"

    if json_report.exists():
        print_success(f"JSON Report: {json_report}")


@click.command()
@click.option("--tags", "-t", multiple=True, help="Run scenarios with specific tags (e.g., @smoke)")
@click.option("--feature", "-f", help="Run specific feature file")
@click.option("--env", "-e", default="dev", help="Environment to run tests (dev, staging, prod)")
@click.option(
    "--report",
    "-r",
    type=click.Choice(["local", "reportportal", "all"]),
    default="all",
    help="Report output mode",
)
@click.option("--parallel", "-p", type=int, default=1, help="Number of parallel workers")
@click.option("--headless/--headed", default=False, help="Run browser in headless mode")
@click.option("--dry-run", is_flag=True, help="Validate scenarios without execution")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-banner", is_flag=True, help="Hide banner")
def run_command(
        tags: tuple[str, ...],
        feature: Optional[str],
        env: str,
        report: str,
        parallel: int,
        headless: bool,
        dry_run: bool,
        debug: bool,
        verbose: bool,
        no_banner: bool,
) -> None:
    """Run test scenarios with specified configuration.

    \b
    Examples:
      nemesis run                              Run all tests
      nemesis run --tags @smoke                Run smoke tests
      nemesis run --feature login.feature      Run specific feature
      nemesis run --env prod --headless        Run in production
      nemesis run --parallel 4 --report all    Parallel execution

    \b
    Tag Expressions:
      @smoke                Single tag
      @smoke,@regression    Multiple tags (OR)
      @smoke and @critical  Tag intersection (AND)
      @smoke and not @wip   Tag exclusion
    """
    try:
        # Load configuration
        config_loader = ConfigLoader()

        if not config_loader.config_exists():
            print_error("Configuration not found")
            console.print("[dim]Run [bold]nemesis init[/bold] to initialize configuration[/dim]\n")
            sys.exit(1)

        config = config_loader.load()

        # Show banner
        if not no_banner and not dry_run:
            try:
                print_banner(compact=True)
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                # Fallback for encoding issues
                console.print("[bold dark_orange]NEMESIS[/bold dark_orange] [dim]Test Automation Framework[/dim]")
                LOGGER.debug(f"Banner encoding fallback: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # Always re-raise these to allow proper program termination
                # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                raise
            except (OSError, IOError) as e:
                # Terminal/IO errors
                console.print("[bold dark_orange]NEMESIS[/bold dark_orange] [dim]Test Automation Framework[/dim]")
                LOGGER.debug(f"Banner IO fallback: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
            console.print()

        # Show configuration
        if not dry_run:
            print_step("Preparing test execution...")
            console.print()
            show_configuration_table(
                env=env,
                report=report,
                headless=headless,
                debug=debug,
                parallel=parallel,
                tags=tags,
                feature=feature,
            )
            console.print()

        # Create executor
        executor = TestExecutor(
            tags=list(tags),
            feature=feature,
            env=env,
            report_mode=report,
            parallel=parallel,
            headless=headless,
            dry_run=dry_run,
            debug=debug,
            verbose=verbose,
            config=config,
        )

        # Execute tests
        print_step("Running tests...")
        console.print()

        exit_code = executor.execute()

        # Show summary
        console.print()
        if exit_code == 0:
            print_success("All tests passed!")
        else:
            print_error("Some tests failed")

        if not dry_run:
            console.print()
            show_execution_summary(env=env, report=report, exit_code=exit_code)

            # Finalize reports after execution
            # Note: ReportPortal finalization happens in after_all hook (same process)
            # Local report finalization can happen here if needed
            if report in ["local", "all"]:
                # Only finalize local reports here (ReportPortal is finalized in after_all hook)
                # This prevents duplicate finalization
                try:
                    from nemesis.infrastructure.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                    env_manager = _get_env_manager()
                    if env_manager and env_manager.reporting_env.report_manager:
                        # Local report finalization (HTML generation) can happen here if not done in after_all
                        # But for now, both are handled in after_all hook
                        pass
                except (ImportError, AttributeError, RuntimeError) as e:
                    # Ignore errors during optional report finalization
                    LOGGER.debug(f"Optional report finalization skipped: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
                except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                    # Always re-raise these to allow proper program termination
                    # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                    raise
                _show_report_path()

        console.print()
        sys.exit(exit_code)

    except SystemExit:  # pylint: disable=try-except-raise
        # Re-raise SystemExit to allow proper program termination
        # NOTE: SystemExit must propagate to allow proper exit code handling
        LOGGER.debug("SystemExit caught in run_command, propagating", module=__name__, function="run_command")
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Test execution interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError) as e:
        # File system errors during test execution
        LOGGER.error(f"Execution failed - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
        print_error(f"Execution failed - I/O error: {e}")
        if debug:
            console.print_exception()
        sys.exit(1)
    except (ValueError, TypeError) as e:
        # Configuration or parameter errors
        LOGGER.error(f"Execution failed - Invalid configuration: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
        print_error(f"Execution failed - Invalid configuration: {e}")
        if debug:
            console.print_exception()
        sys.exit(1)
    except RuntimeError as e:
        # Runtime execution errors
        LOGGER.error(f"Execution failed - Runtime error: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
        print_error(f"Execution failed - Runtime error: {e}")
        if debug:
            console.print_exception()
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Behave, Playwright, or other test framework components
        # NOTE: Test frameworks may raise various exceptions we cannot fully predict
        LOGGER.error(f"Execution failed: {e}", traceback=traceback.format_exc(), module=__name__, function="run_command")
        print_error(f"Execution failed: {e}")
        if debug:
            console.print_exception()
        sys.exit(1)

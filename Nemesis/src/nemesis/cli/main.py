"""Nemesis CLI - Main Entry Point."""
import sys
import traceback

import click
from rich.console import Console

from nemesis.infrastructure.logging import Logger
from .ascii_art import print_banner
from .commands.clean import clean_command
from .commands.init import init_command
from .commands.list import list_command
from .commands.open import open_command
from .commands.run import run_command
from .commands.validate import validate_command
from .ui.styles import  error_style
console = Console()
LOGGER = Logger.get_instance({})


@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0", prog_name="nemesis")
@click.pass_context
def cli(ctx) -> None:
    """Nemesis - Modern BDD Test Automation Framework

    Built with Playwright, Behave, and ReportPortal.

    \b
    Quick Start:
      nemesis init              Initialize configuration
      nemesis run               Run all tests
      nemesis run --tags @smoke Run specific tests
      nemesis list              View test results
      nemesis clean             Clean old reports

    \b
    Documentation:
      https://github.com/your-org/nemesis
    """
    if ctx.invoked_subcommand is None:
        try:
            print_banner()
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # Always re-raise these to allow proper program termination
            # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
            raise
        except (UnicodeEncodeError, UnicodeDecodeError, OSError) as e:
            # Fallback for encoding issues or terminal problems
            console.print("[bold dark_orange]NEMESIS[/bold dark_orange] [dim]Test Automation Framework[/dim]")
            LOGGER.debug(f"Banner fallback due to: {e}", traceback=traceback.format_exc(), module=__name__)
        console.print("\n[dim]Use [bold]nemesis --help[/bold] to see available commands[/dim]\n")


# Register commands
cli.add_command(init_command, name="init")
cli.add_command(run_command, name="run")
cli.add_command(list_command, name="list")
cli.add_command(clean_command, name="clean")
cli.add_command(validate_command, name="validate")
cli.add_command(open_command, name="open")


def main():
    """Main entry point with error handling."""
    try:
        # Set UTF-8 encoding for Windows console
        if sys.platform == "win32":
            import codecs  # pylint: disable=import-outside-toplevel
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

        # Call cli without context - click handles it automatically when standalone_mode=True
        cli(standalone_mode=True)  # pylint: disable=no-value-for-parameter
    except SystemExit:  # pylint: disable=try-except-raise
        # Re-raise SystemExit to allow proper program termination
        # NOTE: SystemExit must propagate to allow proper exit code handling
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError) as e:
        # File/OS related errors during initialization
        LOGGER.error(f"Fatal I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="main")
        console.print(f"\n{error_style('Fatal I/O error:')} {e}\n")
        sys.exit(1)
    except (ValueError, TypeError, RuntimeError) as e:
        # Configuration or runtime errors
        LOGGER.error(f"Fatal error: {e}", traceback=traceback.format_exc(), module=__name__, function="main")
        console.print(f"\n{error_style('Fatal error:')} {e}\n")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from click framework and other unknown sources
        # NOTE: Click framework may raise various exceptions we cannot predict
        LOGGER.error(f"Fatal error: {e}", traceback=traceback.format_exc(), module=__name__, function="main")
        console.print(f"\n{error_style('Fatal error:')} {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

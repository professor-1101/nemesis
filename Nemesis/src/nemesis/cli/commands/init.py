"""CLI init command - Initialize Nemesis configuration."""
import shutil
import sys
import traceback
from pathlib import Path
import importlib.resources as resources

import click

from ..ascii_art import print_banner, print_error, print_step, print_success
from .common import console, LOGGER as logger


@click.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing configuration")
def init_command(force: bool) -> None:
    """Initialize Nemesis configuration in the current directory."""
    try:
        print_banner(compact=True)
        console.print()

        print_step("Initializing Nemesis configuration...")
        console.print()

        conf_dir = Path.cwd() / "conf"

        if conf_dir.exists() and not force:
            print_error("Configuration directory already exists")
            console.print("[dim]Use --force to overwrite existing configuration[/dim]\n")
            sys.exit(1)

        conf_dir.mkdir(exist_ok=True)
        print_success(f"Created configuration directory: {conf_dir}")

        config_files = [
            "playwright.yaml",
            "reportportal.yaml",
            "behave.ini",
            "logging.yaml",
            "reporting.yaml",
        ]

        for filename in config_files:
            destination = conf_dir / filename
            if destination.exists() and not force:
                print_step(f"Skipping {filename} (already exists)")
                continue

            try:
                template_file = resources.files("nemesis.cli.templates").joinpath(filename)
                with resources.as_file(template_file) as src_path:
                    shutil.copy(src_path, destination)
                    print_success(f"Created {filename}")
            except FileNotFoundError:
                logger.warning(f"Template not found: {filename}", module=__name__, function="init_command", template_file=filename)
                print_error(f"Template not found: {filename}")
            except (OSError, IOError, shutil.Error) as ex:
                # File operation errors
                logger.error(f"Failed to copy {filename}: {ex}", traceback=traceback.format_exc(), module=__name__, function="init_command", template_file=filename)
                print_error(f"Failed to copy {filename}: {ex}")
            except (ValueError, TypeError) as ex:
                # Invalid path or type errors
                logger.error(f"Failed to copy {filename} - Invalid path: {ex}", traceback=traceback.format_exc(), module=__name__, function="init_command", template_file=filename)
                print_error(f"Failed to copy {filename} - Invalid path: {ex}")

        console.print()
        print_success("Configuration initialized successfully!\n")

        console.print("[bold cyan]Next steps:[/bold cyan]")
        console.print("  [dim]1.[/dim] Edit [cyan]conf/reportportal.yaml[/cyan] with your credentials")
        console.print("  [dim]2.[/dim] Run [cyan]nemesis run[/cyan] to execute tests")
        console.print("  [dim]3.[/dim] View results with [cyan]nemesis list[/cyan]")
        console.print()

    except SystemExit:  # pylint: disable=try-except-raise
        # Re-raise SystemExit to allow proper program termination
        # NOTE: SystemExit must propagate to allow proper exit code handling
        logger.debug("SystemExit caught in init_command, propagating", module=__name__, function="init_command")
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Initialization interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError, PermissionError) as e:
        # File system errors during directory/file creation
        logger.error(f"Initialization failed - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="init_command")
        print_error(f"Initialization failed - I/O error: {e}")
        sys.exit(1)
    except (ValueError, TypeError) as e:
        # Invalid configuration or path errors
        logger.error(f"Initialization failed - Invalid input: {e}", traceback=traceback.format_exc(), module=__name__, function="init_command")
        print_error(f"Initialization failed - Invalid input: {e}")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from importlib.resources or Rich library
        # NOTE: importlib.resources API may raise various exceptions we cannot predict
        logger.error(f"Initialization failed: {e}", traceback=traceback.format_exc(), module=__name__, function="init_command")
        print_error(f"Initialization failed: {e}")
        sys.exit(1)

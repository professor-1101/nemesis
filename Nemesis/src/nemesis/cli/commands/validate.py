"""CLI validate command - Validate Nemesis configuration."""

import sys
import traceback
from pathlib import Path

import click
from rich.table import Table

from nemesis.infrastructure.config import ConfigLoader, ConfigValidator
from ..ascii_art import print_banner, print_error, print_step, print_success
from .common import console, LOGGER as logger


@click.command()
@click.option("--config-dir", "-c", type=click.Path(exists=True), help="Configuration directory path")
def validate_command(config_dir: Path | None) -> None:
    """Validate Nemesis configuration files.

    \b
    Examples:
      nemesis validate              Validate current directory configuration
      nemesis validate -c /path    Validate specific config directory
    """
    try:
        print_banner(compact=True)
        console.print()

        print_step("Validating Nemesis configuration...")
        console.print()

        # Find config directory
        if config_dir:
            config_path = Path(config_dir)
        else:
            # Try common locations
            for dirname in ["conf", "config", "configs"]:
                path = Path.cwd() / dirname
                if path.exists():
                    config_path = path
                    break
            else:
                print_error("Configuration directory not found")
                console.print("[dim]Run [bold]nemesis init[/bold] to initialize configuration[/dim]\n")
                sys.exit(1)

        console.print(f"[cyan]Config directory:[/cyan] {config_path}")
        console.print()

        # Validate files
        table = Table(title="Configuration Files", show_header=True, header_style="bold cyan")
        table.add_column("File", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        issues = []

        # Check required files
        required_files = ["playwright.yaml", "reporting.yaml"]
        for filename in required_files:
            file_path = config_path / filename
            if file_path.exists():
                table.add_row(filename, "✅", "Found")
            else:
                table.add_row(filename, "❌", "Missing")
                issues.append(f"Required file missing: {filename}")

        # Check optional files
        optional_files = [
            ("logging.yaml", "Logging configuration"),
            ("reportportal.yaml", "ReportPortal configuration"),
            ("behave.ini", "Behave configuration"),
        ]

        for filename, description in optional_files:
            file_path = config_path / filename
            if file_path.exists():
                table.add_row(filename, "✅", description)
            else:
                table.add_row(filename, "⚠️", f"{description} (optional)")

        console.print(table)
        console.print()

        # Validate schema
        if not issues:
            print_step("Validating configuration schemas...")

            config_loader = ConfigLoader(config_dir=config_path)
            config = config_loader.load()

            validator = ConfigValidator()
            result = validator.validate(config)

            if result["valid"]:
                console.print()
                print_success("Configuration validation passed!")
                console.print()
                sys.exit(0)
            else:
                console.print()
                print_error("Configuration validation failed:")
                console.print()
                for error in result["errors"]:
                    console.print(f"  [red]•[/red] {error}")
                    issues.append(error)

        # Summary
        console.print()
        if issues:
            print_error(f"Found {len(issues)} issue(s)")
            sys.exit(1)
        else:
            print_success("Configuration is valid!")
            console.print()
            sys.exit(0)

    except SystemExit:  # pylint: disable=try-except-raise
        # Re-raise SystemExit to allow proper program termination
        # NOTE: SystemExit must propagate to allow proper exit code handling
        logger.debug("SystemExit caught in validate_command, propagating", module=__name__, function="validate_command")
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Validation interrupted by user[/yellow]")
        sys.exit(130)
    except (OSError, IOError, FileNotFoundError) as e:
        # File system errors during validation
        logger.error(f"Validation failed - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, function="validate_command")
        print_error(f"Validation failed - I/O error: {e}")
        if "--debug" in sys.argv:
            console.print_exception()
        sys.exit(1)
    except (ValueError, TypeError) as e:
        # Configuration parsing errors
        logger.error(f"Validation failed - Invalid configuration: {e}", traceback=traceback.format_exc(), module=__name__, function="validate_command")
        print_error(f"Validation failed - Invalid configuration: {e}")
        if "--debug" in sys.argv:
            console.print_exception()
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch-all for unexpected errors from Rich library or config parsing
        # NOTE: ConfigLoader and Rich may raise various exceptions we cannot predict
        logger.error(f"Validation failed: {e}", traceback=traceback.format_exc(), module=__name__, function="validate_command")
        print_error(f"Validation failed: {e}")
        if "--debug" in sys.argv:
            console.print_exception()
        sys.exit(1)

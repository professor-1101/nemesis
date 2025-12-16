"""ASCII art and branding for Nemesis CLI """
import traceback

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from nemesis.core.logging import Logger

console = Console()
LOGGER = Logger.get_instance({})

NEMESIS_BANNER = """
  ███╗   ██╗███████╗███╗   ███╗███████╗███████╗██╗███████╗
  ████╗  ██║██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝
  ██╔██╗ ██║█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗
  ██║╚██╗██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║
  ██║ ╚████║███████╗██║ ╚═╝ ██║███████╗███████║██║███████║
  ╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝
"""

def print_banner(compact: bool = False) -> None:
    """Print Nemesis banner"""
    try:
        text = Text(NEMESIS_BANNER, style="bold orange3")
        if compact:
            panel = Panel(
                text,
                title="[bold white]NEMESIS[/bold white]",
                subtitle="[dim]Test Automation[/dim]",
                border_style="dark_orange",
                padding=(0, 1),
                expand=False
            )
        else:
            panel = Panel(
                text,
                title="[bold white]Test Automation Framework[/bold white]",
                subtitle="[dim]v1.0.0 | Playwright + Behave + ReportPortal[/dim]",
                border_style="dark_orange",
                padding=(0, 1),
                expand=False
            )
        console.print(panel)
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        # Fallback for non-UTF8 terminals or encoding issues
        console.print("[bold dark_orange]NEMESIS[/bold dark_orange] [dim]Test Automation Framework[/dim]")
        console.print("[dim]" + "─" * 60 + "[/dim]")
        LOGGER.debug(f"Banner encoding fallback: {e}", traceback=traceback.format_exc(), module=__name__, function="print_banner")
    except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
        # Always re-raise these to allow proper program termination
        # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
        raise
    except (OSError, IOError) as e:
        # Terminal/IO errors
        console.print("[bold dark_orange]NEMESIS[/bold dark_orange] [dim]Test Automation Framework[/dim]")
        LOGGER.debug(f"Banner IO fallback: {e}", traceback=traceback.format_exc(), module=__name__, function="print_banner")

def print_step(message: str) -> None:
    """Print step message """
    console.print(f"[dark_orange]→[/dark_orange] {message}")

def print_success(message: str) -> None:
    """Print success message """
    console.print(f"[green]✓[/green] {message}")

def print_error(message: str) -> None:
    """Print error message """
    console.print(f"[red]✗[/red] {message}")

"""Common utilities for CLI commands."""

from rich.console import Console
from nemesis.core.logging import Logger

# Shared console and logger instances for CLI commands
console = Console()
LOGGER = Logger.get_instance({})

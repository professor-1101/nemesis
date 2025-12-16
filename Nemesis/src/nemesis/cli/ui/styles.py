"""Color styles and themes."""

# Text styles
def success_style(text: str) -> str:
    """Format text with success style."""
    return f"[green]{text}[/green]"


def error_style(text: str) -> str:
    """Format text with error style."""
    return f"[red]{text}[/red]"


def warning_style(text: str) -> str:
    """Format text with warning style."""
    return f"[yellow]{text}[/yellow]"


def info_style(text: str) -> str:
    """Format text with info style."""
    return f"[cyan]{text}[/cyan]"

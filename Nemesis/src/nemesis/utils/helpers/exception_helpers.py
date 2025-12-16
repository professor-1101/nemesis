"""Helper functions for consistent exception handling patterns."""

from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar('T')


def handle_keyboard_system_exit(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to consistently handle KeyboardInterrupt and SystemExit.
    
    Usage:
        @handle_keyboard_system_exit
        def some_function():
            try:
                ...
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                raise  # Always re-raise these
    """
    return func


def ensure_directory_exists(file_path: Any, execution_id: str = "") -> None:  # pylint: disable=unused-argument
    """Ensure directory exists for file path, handling KeyboardInterrupt/SystemExit.
    
    Args:
        file_path: Path object or string
        execution_id: Optional execution ID for path construction (kept for API compatibility)
    """
    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except KeyboardInterrupt:
        raise
    except SystemExit:
        raise

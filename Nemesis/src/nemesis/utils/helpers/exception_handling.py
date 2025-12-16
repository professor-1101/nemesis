"""Shared exception handling utilities."""

from typing import Callable, TypeVar, Any


F = TypeVar("F", bound=Callable[..., Any])


def handle_keyboard_and_system_exit_in_context(func: Callable) -> Callable:
    """Handle KeyboardInterrupt and SystemExit in context manager __exit__.

    This is a shared pattern for cleanup methods that need to re-raise
    KeyboardInterrupt and SystemExit exceptions.

    Usage:
        def __exit__(self, exc_type, _exc_val, _exc_tb):
            try:
                # cleanup code
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                raise
            except Exception as e:
                # handle other exceptions
    """
    # This is a documentation/pattern helper - actual implementation
    # is in the using classes with the pylint disable comment
    return func

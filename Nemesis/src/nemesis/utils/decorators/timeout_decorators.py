"""Timeout decorators."""
import functools
import signal
import time
import traceback
from typing import Any, Callable, TypeVar

from nemesis.shared.exceptions.network_exceptions import NemesisTimeoutError
from nemesis.infrastructure.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])
LOGGER = Logger.get_instance({})


def timeout(seconds: float) -> Callable[[F], F]:
    """Timeout decorator."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try signal-based timeout (Unix only)
            try:
                import platform  # pylint: disable=import-outside-toplevel
                if platform.system() != "Windows":
                    return _timeout_with_signal(func, seconds, args, kwargs)
            except (ImportError, AttributeError) as e:
                # Platform or signal module errors - fallback to time check
                LOGGER.debug(f"Signal-based timeout not available: {e}", traceback=traceback.format_exc(), module=__name__, function="timeout")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from platform or signal operations
                # NOTE: platform or signal operations may raise various exceptions we cannot predict
                LOGGER.debug(f"Signal-based timeout failed: {e}", traceback=traceback.format_exc(), module=__name__, function="timeout")

            # Fallback: time-based check (doesn't interrupt)
            LOGGER.warning(
                f"Signal-based timeout not available, using time check for {func.__name__}"
            )
            return _timeout_with_time_check(func, seconds, args, kwargs)

        return wrapper  # type: ignore

    return decorator


def _timeout_with_signal(
    func: Callable,
    seconds: float,
    args: tuple,
    kwargs: dict
) -> Any:
    """Timeout using signal (Unix only)."""
    def timeout_handler(_signum, _frame):
        raise NemesisTimeoutError(f"Function {func.__name__} timed out after {seconds}s")

    # Set signal handler
    # SIGALRM is only available on Unix systems, not Windows
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)  # pylint: disable=no-member
    signal.alarm(int(seconds))  # pylint: disable=no-member

    try:
        result = func(*args, **kwargs)
        return result
    finally:
        # Restore handler
        signal.alarm(0)  # pylint: disable=no-member
        signal.signal(signal.SIGALRM, old_handler)  # pylint: disable=no-member


def _timeout_with_time_check(
    func: Callable,
    seconds: float,
    args: tuple,
    kwargs: dict
) -> Any:
    """Timeout using time check (fallback)."""
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start_time

    if elapsed > seconds:
        raise NemesisTimeoutError(f"Function {func.__name__} took {elapsed:.2f}s, limit was {seconds}s")

    LOGGER.debug(
        f"Function {func.__name__} completed in {elapsed:.2f}s"
    )

    return result

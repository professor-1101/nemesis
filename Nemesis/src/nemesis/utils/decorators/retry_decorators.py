"""Retry decorators."""

import functools
import time
from typing import Any, Callable, TypeVar

from nemesis.core.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])
LOGGER = Logger.get_instance({})


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """Retry decorator for flaky operations."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        LOGGER.warning(
                            f"Attempt {attempt}/{max_attempts} failed for "
                            f"{func.__name__}: {e}. Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        LOGGER.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper  # type: ignore

    return decorator

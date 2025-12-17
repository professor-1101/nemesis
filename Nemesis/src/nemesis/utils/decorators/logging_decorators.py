"""Logging decorators."""

import functools
import time
from typing import Any, Callable, TypeVar

from nemesis.infrastructure.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])
LOGGER = Logger.get_instance({})


def log_execution(
    log_args: bool = False,
    log_result: bool = False
) -> Callable[[F], F]:
    """Log function execution time and optionally args/result."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            # Log function call
            if log_args:
                args_str = ", ".join(repr(a) for a in args)
                kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                LOGGER.debug(f"Executing: {func.__name__}({all_args})")
            else:
                LOGGER.debug(f"Executing: {func.__name__}")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                if log_result:
                    result_str = repr(result)
                    if len(result_str) > 100:
                        result_str = result_str[:97] + "..."
                    LOGGER.debug(
                        f"Completed: {func.__name__} ({elapsed:.3f}s) → {result_str}"
                    )
                else:
                    LOGGER.debug(f"Completed: {func.__name__} ({elapsed:.3f}s)")

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                LOGGER.error(
                    f"Failed: {func.__name__} ({elapsed:.3f}s) - {type(e).__name__}: {e}"
                )
                raise

        return wrapper  # type: ignore

    return decorator

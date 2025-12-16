"""Safety decorators."""

import functools
from typing import Any, Callable, TypeVar

from nemesis.core.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])
LOGGER = Logger.get_instance({})


def safe_execute(
    default: Any = None,
    log_exceptions: bool = True,
    suppress_exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """Safe execution decorator that catches exceptions."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except suppress_exceptions as e:
                if log_exceptions:
                    LOGGER.warning(
                        f"Exception in {func.__name__}: {type(e).__name__}: {e}"
                    )
                return default
            except Exception as e:
                if log_exceptions:
                    LOGGER.error(
                        f"Unexpected exception in {func.__name__}: {type(e).__name__}: {e}"
                    )
                raise

        return wrapper  # type: ignore

    return decorator

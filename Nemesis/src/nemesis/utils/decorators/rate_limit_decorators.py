"""Rate limiting decorators."""

import functools
import time
from typing import Any, Callable, TypeVar

from nemesis.core.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])
LOGGER = Logger.get_instance({})


def rate_limit(calls: int, period: float) -> Callable[[F], F]:
    """Rate limit decorator to prevent too frequent calls."""

    def decorator(func: F) -> F:
        call_times: list[float] = []

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()

            # Remove old calls outside the period
            while call_times and call_times[0] < now - period:
                call_times.pop(0)

            # Check if rate limit exceeded
            if len(call_times) >= calls:
                sleep_time = period - (now - call_times[0])
                if sleep_time > 0:
                    LOGGER.warning(
                        f"Rate limit reached for {func.__name__}, "
                        f"sleeping {sleep_time:.1f}s"
                    )
                    time.sleep(sleep_time)

            # Record this call
            call_times.append(time.time())

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator

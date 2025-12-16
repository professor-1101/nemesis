"""Cache decorators."""

import functools
from typing import Any, Callable, TypeVar

from nemesis.core.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])
LOGGER = Logger.get_instance({})


def memoize(max_size: int = 128) -> Callable[[F], F]:
    """Simple memoization decorator with size limit."""

    def decorator(func: F) -> F:
        cache: dict[tuple, Any] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key
            key = (args, tuple(sorted(kwargs.items())))

            # Check cache
            if key in cache:
                LOGGER.debug(f"Cache hit for {func.__name__}")
                return cache[key]

            # Compute result
            result = func(*args, **kwargs)

            # Store in cache (with size limit)
            if len(cache) >= max_size:
                # Remove oldest entry (FIFO)
                cache.pop(next(iter(cache)))

            cache[key] = result
            return result

        return wrapper  # type: ignore

    return decorator

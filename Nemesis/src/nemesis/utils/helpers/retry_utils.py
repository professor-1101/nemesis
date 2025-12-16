"""Retry utility functions."""

import time
from typing import Any, Callable, Tuple


class RetryUtils:
    """Retry utility functions."""

    @staticmethod
    def retry_on_exception(
        func: Callable,
        max_attempts: int = 3,
        delay: float = 1.0,
        exceptions: Tuple = (Exception,)
    ) -> Any:
        """Simple retry helper function."""
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts:
                    time.sleep(delay)

        raise last_exception

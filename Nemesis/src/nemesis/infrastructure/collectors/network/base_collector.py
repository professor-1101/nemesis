"""Base collector with timestamp support for network collectors."""
from time import time


class BaseCollector:
    """Base class for network collectors with timestamp support."""

    @staticmethod
    def _get_timestamp() -> float:
        """
        Get current timestamp in milliseconds.

        Returns:
            Current timestamp in milliseconds
        """
        return time() * 1000

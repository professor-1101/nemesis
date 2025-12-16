"""Time utility functions."""

from datetime import datetime


class TimeUtils:
    """Time utility functions."""

    @staticmethod
    def generate_timestamp(format_str: str = "%Y-%m-%d_%H-%M-%S") -> str:
        """Generate timestamp string."""
        return datetime.now().strftime(format_str)

    @staticmethod
    def format_duration(seconds: float, precision: int = 2) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.{precision}f}s"
        if seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.{precision}f}m"
        if seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.{precision}f}h"
        days = seconds / 86400
        return f"{days:.{precision}f}d"

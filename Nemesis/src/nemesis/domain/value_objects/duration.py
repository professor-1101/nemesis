"""Duration Value Object - Type-safe duration with formatting"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Duration:
    """
    Value Object for Duration

    Immutable duration representation with formatting utilities.
    Replaces primitive float with type-safe object.

    DDD Pattern: Value Object
    - Immutable
    - Self-formatting
    - Business logic encapsulated (formatting rules)
    """

    seconds: float

    def __post_init__(self) -> None:
        """Validate duration"""
        if self.seconds < 0:
            raise ValueError(f"Duration cannot be negative: {self.seconds}")

    @classmethod
    def zero(cls) -> Duration:
        """Create zero duration"""
        return cls(0.0)

    @classmethod
    def from_milliseconds(cls, milliseconds: Union[int, float]) -> Duration:
        """Create duration from milliseconds"""
        return cls(milliseconds / 1000.0)

    @classmethod
    def from_seconds(cls, seconds: Union[int, float]) -> Duration:
        """Create duration from seconds"""
        return cls(float(seconds))

    def to_milliseconds(self) -> int:
        """Convert to milliseconds (rounded)"""
        return int(self.seconds * 1000)

    def to_seconds(self) -> float:
        """Get duration in seconds"""
        return self.seconds

    def format_short(self) -> str:
        """
        Format duration in short form

        Examples:
        - 0.5s
        - 2.3s
        - 125.4s
        """
        return f"{self.seconds:.1f}s"

    def format_human(self) -> str:
        """
        Format duration in human-readable form

        Examples:
        - 500ms (for < 1 second)
        - 2.3s (for < 60 seconds)
        - 1m 30s (for >= 60 seconds)
        - 1h 5m 30s (for >= 3600 seconds)
        """
        if self.seconds < 1:
            return f"{int(self.seconds * 1000)}ms"

        if self.seconds < 60:
            return f"{self.seconds:.1f}s"

        minutes = int(self.seconds // 60)
        remaining_seconds = self.seconds % 60

        if self.seconds < 3600:
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds:.0f}s"
            return f"{minutes}m"

        hours = int(self.seconds // 3600)
        remaining_minutes = int((self.seconds % 3600) // 60)
        remaining_seconds = self.seconds % 60

        parts = [f"{hours}h"]
        if remaining_minutes > 0:
            parts.append(f"{remaining_minutes}m")
        if remaining_seconds > 0:
            parts.append(f"{remaining_seconds:.0f}s")

        return " ".join(parts)

    def __str__(self) -> str:
        """String representation (human-readable format)"""
        return self.format_human()

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"Duration({self.seconds})"

    def __add__(self, other: Duration) -> Duration:
        """Add two durations"""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot add Duration and {type(other)}")
        return Duration(self.seconds + other.seconds)

    def __lt__(self, other: Duration) -> bool:
        """Less than comparison"""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot compare Duration and {type(other)}")
        return self.seconds < other.seconds

    def __le__(self, other: Duration) -> bool:
        """Less than or equal comparison"""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot compare Duration and {type(other)}")
        return self.seconds <= other.seconds

    def __gt__(self, other: Duration) -> bool:
        """Greater than comparison"""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot compare Duration and {type(other)}")
        return self.seconds > other.seconds

    def __ge__(self, other: Duration) -> bool:
        """Greater than or equal comparison"""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot compare Duration and {type(other)}")
        return self.seconds >= other.seconds

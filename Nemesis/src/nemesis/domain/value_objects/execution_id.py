"""ExecutionId Value Object - Type-safe identifier for test execution"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import re


@dataclass(frozen=True)
class ExecutionId:
    """
    Value Object for Execution ID

    Immutable identifier for test execution with validation.
    Format: exec_YYYYMMDD_HHMMSS (e.g., exec_20250416_143052)

    DDD Pattern: Value Object
    - Immutable (frozen=True)
    - Self-validating
    - Type-safe replacement for string primitives
    """

    value: str

    def __post_init__(self) -> None:
        """Validate execution ID format"""
        if not self.value:
            raise ValueError("ExecutionId cannot be empty")

        if not self.value.startswith("exec_"):
            raise ValueError(f"ExecutionId must start with 'exec_', got: {self.value}")

        # Validate format: exec_YYYYMMDD_HHMMSS
        pattern = r"^exec_\d{8}_\d{6}$"
        if not re.match(pattern, self.value):
            raise ValueError(
                f"ExecutionId must match format 'exec_YYYYMMDD_HHMMSS', got: {self.value}"
            )

    @classmethod
    def generate(cls) -> ExecutionId:
        """Generate a new ExecutionId with current timestamp"""
        now = datetime.now(timezone.utc)
        value = now.strftime("exec_%Y%m%d_%H%M%S")
        return cls(value)

    @classmethod
    def from_string(cls, value: str) -> ExecutionId:
        """Create ExecutionId from string (with validation)"""
        return cls(value)

    def __str__(self) -> str:
        """String representation for display"""
        return self.value

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"ExecutionId('{self.value}')"

    def __hash__(self) -> int:
        """Hash for use in sets/dicts"""
        return hash(self.value)

    def extract_timestamp(self) -> datetime:
        """Extract timestamp from execution ID"""
        # exec_20250416_143052 -> 20250416_143052
        timestamp_str = self.value.replace("exec_", "")
        return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)

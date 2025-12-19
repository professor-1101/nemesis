"""StepStatus Value Object - Type-safe status for test steps"""

from enum import Enum


class StepStatus(str, Enum):
    """
    Value Object for Step Status

    Type-safe enumeration for step execution status.

    DDD Pattern: Value Object (Enum)
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNDEFINED = "UNDEFINED"

    def is_terminal(self) -> bool:
        """Check if this is a final status"""
        return self in {
            StepStatus.PASSED,
            StepStatus.FAILED,
            StepStatus.SKIPPED,
            StepStatus.UNDEFINED,
        }

    def is_successful(self) -> bool:
        """Check if step succeeded"""
        return self == StepStatus.PASSED

    def is_failed(self) -> bool:
        """Check if step failed"""
        return self == StepStatus.FAILED

    @classmethod
    def from_string(cls, status: str) -> "StepStatus":
        """Create StepStatus from string (case-insensitive)"""
        normalized = status.upper()
        try:
            return cls[normalized]
        except KeyError:
            # Handle Behave-specific values
            behave_mapping = {
                "EXECUTING": cls.RUNNING,
                "UNTESTED": cls.PENDING,
            }
            if normalized in behave_mapping:
                return behave_mapping[normalized]

            raise ValueError(f"Invalid step status: {status}")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"StepStatus.{self.name}"

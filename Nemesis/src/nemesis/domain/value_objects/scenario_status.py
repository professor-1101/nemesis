"""ScenarioStatus Value Object - Type-safe status enumeration"""

from enum import Enum
from typing import Set


class ScenarioStatus(str, Enum):
    """
    Value Object for Scenario Status

    Type-safe enumeration for scenario execution status.
    Inherits from str for JSON serialization compatibility.

    DDD Pattern: Value Object (Enum)
    - Immutable
    - Type-safe (no string typos)
    - Ubiquitous Language (domain terminology)
    - Self-documenting
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

    def is_terminal(self) -> bool:
        """Check if this is a final status (no more transitions possible)"""
        return self in {
            ScenarioStatus.PASSED,
            ScenarioStatus.FAILED,
            ScenarioStatus.SKIPPED,
        }

    def is_successful(self) -> bool:
        """Check if scenario succeeded"""
        return self == ScenarioStatus.PASSED

    def is_failed(self) -> bool:
        """Check if scenario failed"""
        return self == ScenarioStatus.FAILED

    def is_running(self) -> bool:
        """Check if scenario is currently running"""
        return self == ScenarioStatus.RUNNING

    @classmethod
    def from_string(cls, status: str) -> "ScenarioStatus":
        """
        Create ScenarioStatus from string (case-insensitive)

        Handles common variations:
        - "PASSED", "passed", "Passed" -> ScenarioStatus.PASSED
        - "FAILED", "failed", "Failed" -> ScenarioStatus.FAILED
        """
        normalized = status.upper()
        try:
            return cls[normalized]
        except KeyError:
            # Handle Behave-specific status values
            behave_mapping = {
                "EXECUTING": cls.RUNNING,
                "UNTESTED": cls.PENDING,
            }
            if normalized in behave_mapping:
                return behave_mapping[normalized]

            raise ValueError(f"Invalid scenario status: {status}")

    @classmethod
    def terminal_statuses(cls) -> Set["ScenarioStatus"]:
        """Get all terminal statuses"""
        return {cls.PASSED, cls.FAILED, cls.SKIPPED}

    def __str__(self) -> str:
        """String representation (returns enum value)"""
        return self.value

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"ScenarioStatus.{self.name}"

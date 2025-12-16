"""Step Entity - Rich domain model with behavior"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from nemesis.domain.value_objects import StepStatus, Duration


@dataclass
class Step:
    """
    Step Entity - Represents a single test step

    DDD Pattern: Entity
    - Has unique identity (step_id)
    - Has lifecycle (pending -> running -> passed/failed)
    - Contains business logic (start, complete, fail)
    - Immutable status transitions
    """

    step_id: str
    name: str
    keyword: str  # Given/When/Then/And/But
    status: StepStatus = field(default=StepStatus.PENDING)
    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    error_message: Optional[str] = field(default=None)

    @classmethod
    def create(cls, name: str, keyword: str = "Given") -> Step:
        """Factory method to create a new step"""
        step_id = f"step_{uuid4().hex[:8]}"
        return cls(step_id=step_id, name=name, keyword=keyword)

    def start(self) -> None:
        """
        Start step execution

        Business Rule: Can only start a pending step
        """
        if self.status != StepStatus.PENDING:
            raise ValueError(f"Cannot start step in status {self.status}")

        self.status = StepStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)

    def complete_successfully(self) -> None:
        """
        Mark step as passed

        Business Rule: Can only complete a running step
        """
        if self.status != StepStatus.RUNNING:
            raise ValueError(f"Cannot complete step in status {self.status}")

        self.status = StepStatus.PASSED
        self.end_time = datetime.now(timezone.utc)

    def fail(self, error_message: str) -> None:
        """
        Mark step as failed

        Business Rule: Can fail from running or pending status
        """
        if self.status.is_terminal():
            raise ValueError(f"Cannot fail step in terminal status {self.status}")

        self.status = StepStatus.FAILED
        self.end_time = datetime.now(timezone.utc)
        self.error_message = error_message

    def skip(self) -> None:
        """Mark step as skipped"""
        if self.status.is_terminal():
            raise ValueError(f"Cannot skip step in terminal status {self.status}")

        self.status = StepStatus.SKIPPED
        if not self.end_time:
            self.end_time = datetime.now(timezone.utc)

    def mark_undefined(self) -> None:
        """Mark step as undefined (no step definition found)"""
        self.status = StepStatus.UNDEFINED
        if not self.end_time:
            self.end_time = datetime.now(timezone.utc)

    def get_duration(self) -> Duration:
        """Calculate step duration"""
        if not self.start_time or not self.end_time:
            return Duration.zero()

        delta = self.end_time - self.start_time
        return Duration.from_seconds(delta.total_seconds())

    def is_completed(self) -> bool:
        """Check if step has completed execution"""
        return self.status.is_terminal()

    def is_successful(self) -> bool:
        """Check if step passed"""
        return self.status.is_successful()

    def is_failed(self) -> bool:
        """Check if step failed"""
        return self.status.is_failed()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "keyword": self.keyword,
            "status": str(self.status),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration().to_seconds(),
            "error_message": self.error_message,
        }

    def __repr__(self) -> str:
        return f"Step(id={self.step_id}, name='{self.name}', status={self.status})"

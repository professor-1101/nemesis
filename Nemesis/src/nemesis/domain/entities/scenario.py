"""Scenario Entity - Rich domain model with business logic"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from nemesis.domain.value_objects import ScenarioStatus, Duration
from nemesis.domain.entities.step import Step


@dataclass
class Scenario:
    """
    Scenario Entity - Represents a BDD scenario

    DDD Pattern: Entity (Aggregate Root)
    - Has unique identity (scenario_id)
    - Manages Step entities (aggregate)
    - Contains business logic and invariants
    - Enforces business rules
    """

    scenario_id: str
    name: str
    feature_name: str
    tags: List[str] = field(default_factory=list)
    status: ScenarioStatus = field(default=ScenarioStatus.PENDING)
    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    steps: List[Step] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, feature_name: str, tags: Optional[List[str]] = None) -> Scenario:
        """Factory method to create a new scenario"""
        scenario_id = f"scenario_{uuid4().hex[:8]}"
        return cls(
            scenario_id=scenario_id,
            name=name,
            feature_name=feature_name,
            tags=tags or [],
        )

    def start(self) -> None:
        """
        Start scenario execution

        Business Rule: Can only start a pending scenario
        """
        if self.status != ScenarioStatus.PENDING:
            raise ValueError(f"Cannot start scenario in status {self.status}")

        self.status = ScenarioStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)

    def add_step(self, step: Step) -> None:
        """
        Add a step to the scenario

        Business Rule: Can only add steps while scenario is not completed
        """
        if self.status.is_terminal():
            raise ValueError(f"Cannot add step to scenario in terminal status {self.status}")

        self.steps.append(step)

    def complete(self) -> None:
        """
        Complete scenario execution

        Business Rule: Scenario status is derived from step statuses
        - All steps passed -> PASSED
        - Any step failed -> FAILED
        - Any step skipped and no failures -> SKIPPED
        """
        if self.status != ScenarioStatus.RUNNING:
            raise ValueError(f"Cannot complete scenario in status {self.status}")

        self.end_time = datetime.now(timezone.utc)

        # Calculate status from steps
        if not self.steps:
            self.status = ScenarioStatus.PASSED
            return

        has_failed = any(step.is_failed() for step in self.steps)
        has_undefined = any(step.status == step.status.UNDEFINED for step in self.steps)
        all_passed = all(step.is_successful() for step in self.steps)

        if has_failed or has_undefined:
            self.status = ScenarioStatus.FAILED
        elif all_passed:
            self.status = ScenarioStatus.PASSED
        else:
            self.status = ScenarioStatus.SKIPPED

    def fail(self) -> None:
        """
        Mark scenario as failed explicitly

        Business Rule: Can fail from any non-terminal status
        """
        if self.status.is_terminal():
            raise ValueError(f"Cannot fail scenario in terminal status {self.status}")

        self.status = ScenarioStatus.FAILED
        self.end_time = datetime.now(timezone.utc)

    def skip(self) -> None:
        """Mark scenario as skipped"""
        if self.status.is_terminal():
            raise ValueError(f"Cannot skip scenario in terminal status {self.status}")

        self.status = ScenarioStatus.SKIPPED
        if not self.end_time:
            self.end_time = datetime.now(timezone.utc)

    def get_duration(self) -> Duration:
        """Calculate scenario duration"""
        if not self.start_time or not self.end_time:
            return Duration.zero()

        delta = self.end_time - self.start_time
        return Duration.from_seconds(delta.total_seconds())

    def is_completed(self) -> bool:
        """Check if scenario has completed"""
        return self.status.is_terminal()

    def is_successful(self) -> bool:
        """Check if scenario passed"""
        return self.status.is_successful()

    def is_failed(self) -> bool:
        """Check if scenario failed"""
        return self.status.is_failed()

    def get_passed_steps_count(self) -> int:
        """Count passed steps"""
        return sum(1 for step in self.steps if step.is_successful())

    def get_failed_steps_count(self) -> int:
        """Count failed steps"""
        return sum(1 for step in self.steps if step.is_failed())

    def get_skipped_steps_count(self) -> int:
        """Count skipped steps"""
        return sum(1 for step in self.steps if step.status == step.status.SKIPPED)

    def has_tag(self, tag: str) -> bool:
        """Check if scenario has a specific tag"""
        return tag in self.tags

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "feature_name": self.feature_name,
            "tags": self.tags,
            "status": str(self.status),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration().to_seconds(),
            "steps": [step.to_dict() for step in self.steps],
            "passed_steps": self.get_passed_steps_count(),
            "failed_steps": self.get_failed_steps_count(),
            "skipped_steps": self.get_skipped_steps_count(),
        }

    def __repr__(self) -> str:
        return f"Scenario(id={self.scenario_id}, name='{self.name}', status={self.status}, steps={len(self.steps)})"

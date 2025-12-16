"""Execution Entity - Aggregate root for test execution"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict

from nemesis.domain.value_objects import ExecutionId, ScenarioStatus, Duration
from nemesis.domain.entities.scenario import Scenario


@dataclass
class Execution:
    """
    Execution Entity - Aggregate Root

    Represents a complete test execution run.

    DDD Pattern: Aggregate Root
    - Has unique identity (ExecutionId value object)
    - Manages Scenario entities
    - Enforces consistency boundaries
    - Contains business logic for execution lifecycle
    """

    execution_id: ExecutionId
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = field(default=None)
    scenarios: List[Scenario] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(cls, execution_id: Optional[ExecutionId] = None) -> Execution:
        """Factory method to create a new execution"""
        if execution_id is None:
            execution_id = ExecutionId.generate()

        return cls(execution_id=execution_id)

    def add_scenario(self, scenario: Scenario) -> None:
        """
        Add a scenario to the execution

        Business Rule: Can only add scenarios while execution is running
        """
        if self.is_completed():
            raise ValueError("Cannot add scenario to completed execution")

        self.scenarios.append(scenario)

    def complete(self) -> None:
        """Complete the execution"""
        if self.is_completed():
            raise ValueError("Execution already completed")

        self.end_time = datetime.now(timezone.utc)

    def is_completed(self) -> bool:
        """Check if execution has completed"""
        return self.end_time is not None

    def get_duration(self) -> Duration:
        """Calculate total execution duration"""
        if not self.end_time:
            # Execution still running
            delta = datetime.now(timezone.utc) - self.start_time
        else:
            delta = self.end_time - self.start_time

        return Duration.from_seconds(delta.total_seconds())

    def get_passed_scenarios_count(self) -> int:
        """Count passed scenarios"""
        return sum(1 for s in self.scenarios if s.is_successful())

    def get_failed_scenarios_count(self) -> int:
        """Count failed scenarios"""
        return sum(1 for s in self.scenarios if s.is_failed())

    def get_skipped_scenarios_count(self) -> int:
        """Count skipped scenarios"""
        return sum(1 for s in self.scenarios if s.status == ScenarioStatus.SKIPPED)

    def get_total_scenarios_count(self) -> int:
        """Get total number of scenarios"""
        return len(self.scenarios)

    def get_total_steps_count(self) -> int:
        """Get total number of steps across all scenarios"""
        return sum(len(s.steps) for s in self.scenarios)

    def get_passed_steps_count(self) -> int:
        """Count passed steps across all scenarios"""
        return sum(s.get_passed_steps_count() for s in self.scenarios)

    def get_failed_steps_count(self) -> int:
        """Count failed steps across all scenarios"""
        return sum(s.get_failed_steps_count() for s in self.scenarios)

    def is_successful(self) -> bool:
        """
        Check if execution succeeded

        Business Rule: Execution is successful if all scenarios passed
        """
        if not self.scenarios:
            return True

        return all(s.is_successful() for s in self.scenarios)

    def has_failures(self) -> bool:
        """Check if execution has any failures"""
        return any(s.is_failed() for s in self.scenarios)

    def get_scenarios_by_feature(self, feature_name: str) -> List[Scenario]:
        """Get all scenarios for a specific feature"""
        return [s for s in self.scenarios if s.feature_name == feature_name]

    def get_scenarios_by_tag(self, tag: str) -> List[Scenario]:
        """Get all scenarios with a specific tag"""
        return [s for s in self.scenarios if s.has_tag(tag)]

    def add_metadata(self, key: str, value: str) -> None:
        """Add metadata to execution"""
        self.metadata[key] = value

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "execution_id": str(self.execution_id),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration().to_seconds(),
            "total_scenarios": self.get_total_scenarios_count(),
            "passed_scenarios": self.get_passed_scenarios_count(),
            "failed_scenarios": self.get_failed_scenarios_count(),
            "skipped_scenarios": self.get_skipped_scenarios_count(),
            "total_steps": self.get_total_steps_count(),
            "passed_steps": self.get_passed_steps_count(),
            "failed_steps": self.get_failed_steps_count(),
            "is_successful": self.is_successful(),
            "metadata": self.metadata,
            "scenarios": [s.to_dict() for s in self.scenarios],
        }

    def __repr__(self) -> str:
        return (
            f"Execution(id={self.execution_id}, "
            f"scenarios={len(self.scenarios)}, "
            f"passed={self.get_passed_scenarios_count()}, "
            f"failed={self.get_failed_scenarios_count()})"
        )

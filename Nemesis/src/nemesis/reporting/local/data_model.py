"""Data models for local reporting."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StepData:
    """Step execution data."""
    name: str
    start_time: datetime
    end_time: datetime | None = None
    status: str = "RUNNING"
    duration: float = 0.0
    logs: list[dict[str, Any]] = field(default_factory=list)
    screenshots: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None
    stack_trace: str | None = None


@dataclass
class ScenarioData:
    """Scenario execution data."""
    name: str
    start_time: datetime
    end_time: datetime | None = None
    status: str = "RUNNING"
    feature_name: str = "Unknown Feature"
    steps: list[StepData] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Calculate scenario duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def passed_steps(self) -> int:
        """Count passed steps."""
        return sum(1 for s in self.steps if s.status == "PASSED")

    @property
    def failed_steps(self) -> int:
        """Count failed steps."""
        return sum(1 for s in self.steps if s.status == "FAILED")


@dataclass
class ExecutionData:
    """Complete execution data."""
    execution_id: str
    start_time: datetime
    end_time: datetime | None = None
    scenarios: list[ScenarioData] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Calculate total duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def passed_scenarios(self) -> int:
        """Count passed scenarios."""
        return sum(1 for s in self.scenarios if s.status == "PASSED")

    @property
    def failed_scenarios(self) -> int:
        """Count failed scenarios."""
        return sum(1 for s in self.scenarios if s.status == "FAILED")

    @property
    def total_steps(self) -> int:
        """Count total steps."""
        return sum(len(s.steps) for s in self.scenarios)

"""Data models for Allure-style reporting."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class Status(Enum):
    """Test status enumeration."""
    PASSED = "passed"
    FAILED = "failed"
    BROKEN = "broken"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


@dataclass
class AllureStepData:
    """Allure step execution data."""
    name: str
    status: Status = Status.UNKNOWN
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    duration: float = 0.0
    attachments: list[dict[str, Any]] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    steps: list['AllureStepData'] = field(default_factory=list)  # Nested steps
    logs: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    error_trace: Optional[str] = None


@dataclass
class AllureScenarioData:
    """Allure scenario/test case data."""
    name: str
    full_name: str
    status: Status = Status.UNKNOWN
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    duration: float = 0.0
    
    # Allure-specific fields
    description: str = ""
    description_html: str = ""
    labels: list[dict[str, str]] = field(default_factory=list)  # epic, feature, story, severity, etc.
    links: list[dict[str, str]] = field(default_factory=list)  # issue, tms, etc.
    parameters: list[dict[str, Any]] = field(default_factory=list)
    
    # Steps and attachments
    steps: list[AllureStepData] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    
    # History and retries
    history_id: Optional[str] = None
    retry: bool = False
    
    # Error information
    error_message: Optional[str] = None
    error_trace: Optional[str] = None
    
    # Additional metadata
    tags: list[str] = field(default_factory=list)
    suite: str = ""
    test_class: str = ""
    test_method: str = ""


@dataclass
class AllureExecutionData:
    """Complete Allure execution data."""
    execution_id: str
    start_time: datetime
    stop_time: Optional[datetime] = None
    
    # Test results
    test_cases: list[AllureScenarioData] = field(default_factory=list)
    
    # Statistics
    total: int = 0
    passed: int = 0
    failed: int = 0
    broken: int = 0
    skipped: int = 0
    unknown: int = 0
    
    # Environment and metadata
    environment: dict[str, Any] = field(default_factory=dict)
    executor: dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Calculate total duration in seconds."""
        if self.stop_time and self.start_time:
            return (self.stop_time - self.start_time).total_seconds()
        return 0.0
    
    def calculate_statistics(self) -> None:
        """Calculate test statistics."""
        self.total = len(self.test_cases)
        self.passed = sum(1 for tc in self.test_cases if tc.status == Status.PASSED)
        self.failed = sum(1 for tc in self.test_cases if tc.status == Status.FAILED)
        self.broken = sum(1 for tc in self.test_cases if tc.status == Status.BROKEN)
        self.skipped = sum(1 for tc in self.test_cases if tc.status == Status.SKIPPED)
        self.unknown = sum(1 for tc in self.test_cases if tc.status == Status.UNKNOWN)


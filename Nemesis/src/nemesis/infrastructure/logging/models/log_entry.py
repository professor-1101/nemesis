"""Log entry model for structured logging."""

import time
import os
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional


@dataclass
class LogEntry:
    """Structured log entry with all required fields."""

    # Core fields
    timestamp: float
    level: str
    message: str

    # Correlation and execution tracking
    correlation_id: Optional[str] = None
    execution_id: Optional[str] = None

    # Context and data
    context: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)

    # System information
    thread_id: Optional[int] = None
    process_id: Optional[int] = None

    # Module and service identification
    module: str = None
    service_name: str = None
    operation_type: str = None

    def __post_init__(self):
        """Initialize default values."""
        if self.context is None:
            self.context = {}
        if self.data is None:
            self.data = {}
        if self.thread_id is None:
            self.thread_id = 0  # Not using threading
        if self.process_id is None:
            self.process_id = os.getpid()

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return asdict(self)

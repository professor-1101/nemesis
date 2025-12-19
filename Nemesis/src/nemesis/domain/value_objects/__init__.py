"""
Domain Value Objects

Value Objects are immutable objects that represent domain concepts.
They have no identity and are defined by their attributes.
"""

from .execution_id import ExecutionId
from .scenario_status import ScenarioStatus
from .step_status import StepStatus
from .duration import Duration

__all__ = [
    "ExecutionId",
    "ScenarioStatus",
    "StepStatus",
    "Duration",
]

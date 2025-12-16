"""
Nemesis Domain Layer

This layer contains the core business logic, independent of any frameworks or infrastructure.

DDD Concepts:
- Entities: Objects with identity and lifecycle (Execution, Scenario, Step)
- Value Objects: Immutable objects defined by their attributes (ExecutionId, Status, Duration)
- Ports: Interfaces that infrastructure must implement (IBrowserDriver, IReporter, etc.)

Clean Architecture:
- This layer has NO dependencies on outer layers
- Outer layers (Application, Infrastructure) depend on THIS layer
- This enables framework independence and testability
"""

# Value Objects
from .value_objects import (
    ExecutionId,
    ScenarioStatus,
    StepStatus,
    Duration,
)

# Entities
from .entities import (
    Step,
    Scenario,
    Execution,
)

# Ports (Interfaces)
from .ports import (
    IBrowserDriver,
    IBrowser,
    IPage,
    IReporter,
    ICollector,
    ILogShipper,
)

__all__ = [
    # Value Objects
    "ExecutionId",
    "ScenarioStatus",
    "StepStatus",
    "Duration",
    # Entities
    "Step",
    "Scenario",
    "Execution",
    # Ports
    "IBrowserDriver",
    "IBrowser",
    "IPage",
    "IReporter",
    "ICollector",
    "ILogShipper",
]

"""
Domain Ports (Interfaces)

Ports define interfaces that infrastructure must implement.
This achieves Dependency Inversion: Core depends on abstractions, not concretions.

DDD Pattern: Ports (Hexagonal Architecture)
- IBrowserDriver: Interface for browser automation
- IReporter: Interface for test reporting
- ICollector: Interface for data collection
- ILogShipper: Interface for log shipping
"""

from .browser_driver import IBrowserDriver, IBrowser, IPage
from .reporter import IReporter
from .collector import ICollector
from .log_shipper import ILogShipper

__all__ = [
    "IBrowserDriver",
    "IBrowser",
    "IPage",
    "IReporter",
    "ICollector",
    "ILogShipper",
]

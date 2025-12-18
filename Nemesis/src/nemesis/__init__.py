"""Nemesis Test Automation Framework."""

__version__ = "1.0.0"

from nemesis.infrastructure.collectors.console import ConsoleCollector
from nemesis.infrastructure.collectors.network import NetworkCollector
from nemesis.infrastructure.collectors.performance.performance_collector import PerformanceCollector
from nemesis.infrastructure.browser import BrowserService
from nemesis.infrastructure.config import ConfigLoader
from nemesis.infrastructure.logging import Logger
from nemesis.reporting.coordinator import ReportCoordinator

__all__ = [
    "BrowserService",
    "ConfigLoader",
    "Logger",
    "ReportCoordinator",
    "ConsoleCollector",
    "NetworkCollector",
    "PerformanceCollector",
]

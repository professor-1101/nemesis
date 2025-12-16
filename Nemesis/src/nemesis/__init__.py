"""Nemesis Test Automation Framework."""

__version__ = "1.0.0"

from nemesis.collectors.console import ConsoleCollector
from nemesis.collectors.network import NetworkCollector
from nemesis.collectors.performance.performance_collector import PerformanceCollector
from nemesis.core.browser import BrowserManager
from nemesis.core.config import ConfigLoader
from nemesis.core.logging import Logger
from nemesis.reporting.manager import ReportManager

__all__ = [
    "BrowserManager",
    "ConfigLoader",
    "Logger",
    "ReportManager",
    "ConsoleCollector",
    "NetworkCollector",
    "PerformanceCollector",
]

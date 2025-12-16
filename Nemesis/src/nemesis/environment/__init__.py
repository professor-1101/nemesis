"""Environment management package for Nemesis framework."""

from .environment_manager import EnvironmentManager
from .browser_environment import BrowserEnvironment
from .reporting_environment import ReportingEnvironment
from .logger_environment import LoggerEnvironment
from .hooks import (
    before_all, after_all, before_feature, after_feature,
    before_scenario, after_scenario, before_step, after_step
)

__all__ = [
    "EnvironmentManager",
    "BrowserEnvironment",
    "ReportingEnvironment",
    "LoggerEnvironment",
    # Hooks
    "before_all", "after_all", "before_feature", "after_feature",
    "before_scenario", "after_scenario", "before_step", "after_step"
]

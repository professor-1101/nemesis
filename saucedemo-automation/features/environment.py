"""Behave environment file for SauceDemo automation.

This file delegates to Nemesis framework hooks for proper lifecycle management.
Following Clean Architecture principles, test projects should use framework hooks
rather than implementing their own lifecycle management.
"""

# Import framework hooks - these handle all lifecycle management
from nemesis.infrastructure.environment.hooks import (
    before_all,
    after_all,
    before_feature,
    after_feature,
    before_scenario,
    after_scenario,
    before_step,
    after_step
)

# Re-export hooks for Behave to discover
# Framework hooks will:
# - Setup EnvironmentCoordinator
# - Manage browser lifecycle via BrowserEnvironment
# - Handle reporting via ReportingEnvironment
# - Manage logging via LoggerEnvironment
# - Load configuration via ConfigLoader
#
# All lifecycle management is handled by the framework.
# Test project only needs to define features, steps, and configs.

__all__ = [
    "before_all",
    "after_all",
    "before_feature",
    "after_feature",
    "before_scenario",
    "after_scenario",
    "before_step",
    "after_step",
]

"""Allure-style HTML report builder for Nemesis framework."""

from .allure_builder import AllureReportBuilder
from .allure_data_model import AllureExecutionData, AllureScenarioData, AllureStepData, Status
from .allure_cli_manager import AllureCLIManager, AllureCLINotInstalledError
from .converter import convert_execution_data_to_allure

__all__ = [
    "AllureReportBuilder",
    "AllureCLIManager",
    "AllureCLINotInstalledError",
    "AllureExecutionData",
    "AllureScenarioData",
    "AllureStepData",
    "Status",
    "convert_execution_data_to_allure",
]


"""Converter from existing data model to Allure data model."""
from pathlib import Path
from typing import Any, Optional

from nemesis.reporting.local.data_model import ExecutionData, ScenarioData, StepData
from .allure_data_model import (
    AllureExecutionData,
    AllureScenarioData,
    AllureStepData,
    Status
)


def convert_execution_data_to_allure(
    execution_data: ExecutionData,
    execution_path: Path
) -> AllureExecutionData:
    """Convert ExecutionData to AllureExecutionData."""
    
    allure_data = AllureExecutionData(
        execution_id=execution_data.execution_id,
        start_time=execution_data.start_time,
        stop_time=execution_data.end_time
    )
    
    # Convert scenarios to test cases
    for scenario in execution_data.scenarios:
        allure_scenario = convert_scenario_to_allure(scenario, execution_path)
        allure_data.test_cases.append(allure_scenario)
    
    # Calculate statistics
    allure_data.calculate_statistics()
    
    # Add environment info
    allure_data.environment = {
        "execution_id": execution_data.execution_id,
        "start_time": execution_data.start_time.isoformat(),
        "stop_time": execution_data.end_time.isoformat() if execution_data.end_time else None,
        "duration": execution_data.duration
    }
    
    return allure_data


def convert_scenario_to_allure(
    scenario: ScenarioData,
    execution_path: Path
) -> AllureScenarioData:
    """Convert ScenarioData to AllureScenarioData."""
    
    # Determine status
    status = _convert_status_to_allure(scenario.status)
    
    # Convert steps
    allure_steps = []
    for step in scenario.steps:
        allure_step = convert_step_to_allure(step, execution_path)
        allure_steps.append(allure_step)
    
    # Extract tags from scenario name or feature
    tags = _extract_tags_from_scenario(scenario)
    
    # Build labels
    labels = _build_labels(scenario, tags)
    
    # Convert attachments
    attachments = _convert_attachments(scenario.attachments, execution_path)
    
    allure_scenario = AllureScenarioData(
        name=scenario.name,
        full_name=f"{scenario.feature_name}::{scenario.name}",
        status=status,
        start_time=scenario.start_time,
        stop_time=scenario.end_time,
        duration=scenario.duration,
        description="",
        description_html="",
        labels=labels,
        links=[],
        parameters=[],
        steps=allure_steps,
        attachments=attachments,
        history_id=None,
        retry=False,
        error_message=_extract_error_message(scenario),
        error_trace=_extract_error_trace(scenario),
        tags=tags,
        suite=scenario.feature_name,
        test_class="",
        test_method=scenario.name
    )
    
    return allure_scenario


def convert_step_to_allure(
    step: StepData,
    execution_path: Path
) -> AllureStepData:
    """Convert StepData to AllureStepData."""
    
    status = _convert_status_to_allure(step.status)
    
    # Convert step attachments
    attachments = _convert_step_attachments(step, execution_path)
    
    allure_step = AllureStepData(
        name=step.name,
        status=status,
        start_time=step.start_time,
        stop_time=step.end_time,
        duration=step.duration,
        attachments=attachments,
        parameters=[],
        steps=[],  # Nested steps can be added later
        logs=[log.get("message", "") for log in step.logs],
        error_message=step.error_message,
        error_trace=step.stack_trace
    )
    
    return allure_step


def _convert_status_to_allure(status: str) -> Status:
    """Convert status string to Allure Status enum."""
    status_upper = status.upper()
    
    if status_upper == "PASSED":
        return Status.PASSED
    elif status_upper == "FAILED":
        return Status.FAILED
    elif status_upper == "SKIPPED":
        return Status.SKIPPED
    elif status_upper in ["ERROR", "BROKEN"]:
        return Status.BROKEN
    else:
        return Status.UNKNOWN


def _extract_tags_from_scenario(scenario: ScenarioData) -> list[str]:
    """Extract tags from scenario name or feature."""
    tags = []
    
    # Try to extract @tags from scenario name
    if "@" in scenario.name:
        import re
        tag_pattern = r'@(\w+)'
        found_tags = re.findall(tag_pattern, scenario.name)
        tags.extend(found_tags)
    
    # Add feature as tag
    if scenario.feature_name:
        tags.append(f"feature:{scenario.feature_name}")
    
    return tags


def _build_labels(scenario: ScenarioData, tags: list[str]) -> list[dict[str, str]]:
    """Build Allure labels from scenario data."""
    labels = []
    
    # Add feature label
    if scenario.feature_name:
        labels.append({
            "name": "feature",
            "value": scenario.feature_name
        })
    
    # Add suite label
    labels.append({
        "name": "suite",
        "value": scenario.feature_name or "Unknown"
    })
    
    # Add severity based on status
    if scenario.status == "FAILED":
        labels.append({"name": "severity", "value": "critical"})
    else:
        labels.append({"name": "severity", "value": "normal"})
    
    # Add tags as labels
    for tag in tags:
        if ":" in tag:
            name, value = tag.split(":", 1)
            labels.append({"name": name, "value": value})
        else:
            labels.append({"name": "tag", "value": tag})
    
    return labels


def _convert_attachments(
    attachments: list[dict[str, Any]],
    execution_path: Path
) -> list[dict[str, Any]]:
    """Convert attachments to Allure format."""
    allure_attachments = []
    
    for att in attachments:
        file_path = Path(att.get("path", ""))
        
        # Make path relative to execution path
        if file_path.is_absolute():
            try:
                relative_path = file_path.relative_to(execution_path)
            except ValueError:
                relative_path = file_path.name
        else:
            relative_path = file_path
        
        allure_attachments.append({
            "name": att.get("description", file_path.name),
            "type": att.get("type", "unknown"),
            "source": str(relative_path).replace('\\', '/'),
            "size": att.get("size", 0)
        })
    
    return allure_attachments


def _convert_step_attachments(
    step: StepData,
    execution_path: Path
) -> list[dict[str, Any]]:
    """Convert step attachments (screenshots) to Allure format."""
    attachments = []
    
    for screenshot in step.screenshots:
        file_path = Path(screenshot.get("path", ""))
        
        # Make path relative
        if file_path.is_absolute():
            try:
                relative_path = file_path.relative_to(execution_path)
            except ValueError:
                relative_path = file_path.name
        else:
            relative_path = file_path
        
        attachments.append({
            "name": screenshot.get("description", "Screenshot"),
            "type": "image/png",
            "source": str(relative_path).replace('\\', '/'),
            "size": 0
        })
    
    return attachments


def _extract_error_message(scenario: ScenarioData) -> Optional[str]:
    """Extract error message from scenario."""
    # Check failed steps for error messages
    for step in scenario.steps:
        if step.status == "FAILED" and step.error_message:
            return step.error_message
    
    # Check scenario logs
    for log in scenario.logs:
        if log.get("level") == "ERROR":
            return log.get("message")
    
    return None


def _extract_error_trace(scenario: ScenarioData) -> Optional[str]:
    """Extract error trace/stack trace from scenario."""
    # Check failed steps for stack traces
    for step in scenario.steps:
        if step.status == "FAILED" and step.stack_trace:
            return step.stack_trace
    
    return None


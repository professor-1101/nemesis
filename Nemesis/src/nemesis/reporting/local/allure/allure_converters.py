"""Allure data converters and utilities."""
import hashlib
from typing import Any

from nemesis.reporting.local.data_model import ScenarioData, StepData
from .allure_data_model import Status


class AllureConverters:
    """Utility class for converting data to Allure format."""

    @staticmethod
    def convert_status(status: str | Any) -> str:
        """Convert status to Allure format.
        
        Args:
            status: Status string or Status enum
            
        Returns:
            Allure status string
        """
        # Handle Status enum or object with .value or .name attribute
        if hasattr(status, 'value'):
            status_str = str(status.value)
        elif hasattr(status, 'name'):
            status_str = str(status.name)
        else:
            status_str = str(status)
        
        status_upper = status_str.upper()
        
        if status_upper == "PASSED":
            return "passed"
        elif status_upper == "FAILED":
            return "failed"
        elif status_upper == "SKIPPED":
            return "skipped"
        elif status_upper in ["ERROR", "BROKEN"]:
            return "broken"
        else:
            return "unknown"
    
    @staticmethod
    def generate_history_id(scenario: ScenarioData) -> str:
        """Generate history ID for test.
        
        Args:
            scenario: Scenario data
            
        Returns:
            History ID string
        """
        full_name = f"{scenario.feature_name}::{scenario.name}"
        return hashlib.md5(full_name.encode()).hexdigest()
    
    @staticmethod
    def build_labels(scenario: ScenarioData) -> list[dict[str, str]]:
        """Build Allure labels.
        
        Args:
            scenario: Scenario data
            
        Returns:
            List of label dictionaries
        """
        labels = [
            {"name": "suite", "value": scenario.feature_name or "Unknown"},
            {"name": "feature", "value": scenario.feature_name or "Unknown"},
        ]
        
        # Add severity based on status
        if scenario.status == "FAILED":
            labels.append({"name": "severity", "value": "critical"})
        else:
            labels.append({"name": "severity", "value": "normal"})
        
        # Add tags if available
        if hasattr(scenario, 'tags') and scenario.tags:
            for tag in scenario.tags:
                labels.append({"name": "tag", "value": tag})
        
        return labels
    
    @staticmethod
    def build_status_details(scenario: ScenarioData) -> dict[str, str] | None:
        """Build status details for failed tests.
        
        Args:
            scenario: Scenario data
            
        Returns:
            Status details dictionary or None
        """
        if scenario.status != "FAILED":
            return None
        
        # Find error message from failed steps
        error_message = None
        error_trace = None
        
        for step in scenario.steps:
            if step.status == "FAILED":
                error_message = step.error_message or "Test failed"
                error_trace = step.stack_trace or ""
                break
        
        if error_message:
            return {
                "message": error_message,
                "trace": error_trace or ""
            }
        
        return None
    
    @staticmethod
    def build_steps(scenario: ScenarioData, attachments_builder) -> list[dict[str, Any]]:
        """Build Allure steps from scenario steps.
        
        Args:
            scenario: Scenario data
            attachments_builder: AllureAttachmentsBuilder instance
            
        Returns:
            List of step dictionaries
        """
        steps = []
        seen_steps = set()  # Track duplicate steps
        
        for step in scenario.steps:
            # Create unique key for step to avoid duplicates
            step_key = f"{step.name}:{step.start_time}:{step.end_time}"
            if step_key in seen_steps:
                continue  # Skip duplicate
            seen_steps.add(step_key)
            
            allure_step = {
                "name": step.name,
                "status": AllureConverters.convert_status(step.status),
                "stage": "finished",
                "start": int(step.start_time.timestamp() * 1000) if step.start_time else None,
                "stop": int(step.end_time.timestamp() * 1000) if step.end_time else None,
                "attachments": attachments_builder.build_step_attachments(step),
                "parameters": [],
                "steps": [],  # Nested steps
            }
            
            # Add status details if failed
            if step.status == "FAILED":
                allure_step["statusDetails"] = {
                    "message": step.error_message or "Step failed",
                    "trace": step.stack_trace or ""
                }
            
            steps.append(allure_step)
        
        return steps


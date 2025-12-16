"""Allure integration using allure-python-commons."""
import json
import uuid
from pathlib import Path
from typing import Any

from nemesis.reporting.local.data_model import ExecutionData, ScenarioData
from .allure_attachments import AllureAttachmentsBuilder
from .allure_metrics import AllureMetricsBuilder
from .allure_converters import AllureConverters


class AllureResultsGenerator:
    """Generate Allure results in JSON format."""

    def __init__(self, results_dir: Path, execution_path: Path):
        """Initialize Allure results generator.
        
        Args:
            results_dir: Directory where Allure results will be saved
            execution_path: Execution directory path (for finding attachments)
        """
        self.results_dir = results_dir
        self.execution_path = execution_path
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize builders
        self.attachments_builder = AllureAttachmentsBuilder(results_dir, execution_path)
        self.metrics_builder = AllureMetricsBuilder(results_dir, execution_path)

    def generate_from_execution_data(self, execution_data: ExecutionData) -> None:
        """Generate Allure results from execution data.
        
        Args:
            execution_data: Execution data from LocalReporter
        """
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generating Allure results for {len(execution_data.scenarios)} scenarios")
        
        # Generate test result files for each scenario
        for scenario in execution_data.scenarios:
            self._generate_test_result(scenario, execution_data)

    def _generate_test_result(self, scenario: ScenarioData, execution_data: ExecutionData) -> None:
        """Generate Allure test result JSON for a scenario.
        
        Args:
            scenario: Scenario data
            execution_data: Execution data (for context)
        """
        # Generate unique UUID for this test
        test_uuid = str(uuid.uuid4())
        
        # Convert status
        status = AllureConverters.convert_status(scenario.status)
        
        # Build test result structure
        test_result = {
            "uuid": test_uuid,
            "name": scenario.name,
            "fullName": f"{scenario.feature_name}::{scenario.name}",
            "historyId": AllureConverters.generate_history_id(scenario),
            "status": status,
            "statusDetails": AllureConverters.build_status_details(scenario),
            "stage": "finished",
            "description": "",
            "descriptionHtml": "",
            "steps": AllureConverters.build_steps(scenario, self.attachments_builder),
            "attachments": self.attachments_builder.build_attachments(scenario),
            "parameters": [],
            "labels": AllureConverters.build_labels(scenario),
            "links": [],
            "start": int(scenario.start_time.timestamp() * 1000) if scenario.start_time else None,
            "stop": int(scenario.end_time.timestamp() * 1000) if scenario.end_time else None,
        }
        
        # Add metrics if available
        metrics = self.metrics_builder.build_metrics(scenario)
        if metrics:
            test_result["testStage"] = "finished"
            # Allure metrics are stored in a separate file in Allure format
            self.metrics_builder.save_metrics_file(test_uuid, metrics)
            # Note: Allure reads metrics from {uuid}-metrics.json file, not from test result JSON
        
        # Save test result JSON
        result_file = self.results_dir / f"{test_uuid}-result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)

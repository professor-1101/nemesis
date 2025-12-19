"""Unit tests for Reporter implementations"""

import pytest
import json
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from nemesis.infrastructure.reporting.json_reporter import JSONReporter
from nemesis.infrastructure.reporting.console_reporter import ConsoleReporter
from nemesis.domain.entities import Execution, Scenario, Step


class TestJSONReporter:
    """Tests for JSONReporter"""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory"""
        return tmp_path / "json_reports"

    @pytest.fixture
    def reporter(self, output_dir):
        """Create JSON reporter"""
        return JSONReporter(output_dir)

    @pytest.fixture
    def sample_execution(self):
        """Create sample execution"""
        execution = Execution.create()

        scenario = Scenario.create("Test Login", "Authentication")
        scenario.start()

        step = Step.create("I am on login page", "Given")
        step.start()
        step.complete_successfully()
        scenario.add_step(step)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        return execution

    def test_initialization_creates_directory(self, reporter, output_dir):
        """Test that initialization creates output directory"""
        assert output_dir.exists()

    def test_start_execution(self, reporter, sample_execution):
        """Test reporting execution start"""
        reporter.start_execution(sample_execution)
        assert reporter._current_execution == sample_execution

    def test_end_execution(self, reporter, sample_execution):
        """Test reporting execution end"""
        reporter.start_execution(sample_execution)
        reporter.end_execution(sample_execution)
        # No exception should be raised

    def test_generate_report_creates_json_file(self, reporter, sample_execution, output_dir):
        """Test generating JSON report"""
        report_path = reporter.generate_report(sample_execution, output_dir)

        assert report_path.exists()
        assert report_path.suffix == ".json"

        # Verify JSON content
        with open(report_path) as f:
            data = json.load(f)

        assert data["total_scenarios"] == 1
        assert data["passed_scenarios"] == 1
        assert data["is_successful"] is True
        assert len(data["scenarios"]) == 1

    def test_generate_report_with_failed_scenario(self, reporter, output_dir):
        """Test generating report with failed scenario"""
        execution = Execution.create()

        scenario = Scenario.create("Test Login", "Authentication")
        scenario.start()

        step = Step.create("I enter invalid credentials", "When")
        step.start()
        step.fail("Invalid credentials")
        scenario.add_step(step)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        report_path = reporter.generate_report(execution, output_dir)

        # Verify JSON content
        with open(report_path) as f:
            data = json.load(f)

        assert data["failed_scenarios"] == 1
        assert data["is_successful"] is False

    def test_start_scenario(self, reporter):
        """Test reporting scenario start"""
        scenario = Scenario.create("Test", "Feature")
        reporter.start_scenario(scenario)
        # No exception should be raised

    def test_end_scenario(self, reporter):
        """Test reporting scenario end"""
        scenario = Scenario.create("Test", "Feature")
        scenario.start()
        scenario.complete()
        reporter.end_scenario(scenario)
        # No exception should be raised

    def test_attach_file(self, reporter):
        """Test attaching file (no-op for JSON reporter)"""
        reporter.attach_file(Path("/tmp/test.png"))
        # No exception should be raised

    def test_log_message(self, reporter):
        """Test logging message (no-op for JSON reporter)"""
        reporter.log_message("Test message", level="INFO")
        # No exception should be raised


class TestConsoleReporter:
    """Tests for ConsoleReporter"""

    @pytest.fixture
    def reporter(self):
        """Create console reporter"""
        return ConsoleReporter()

    @pytest.fixture
    def sample_execution(self):
        """Create sample execution"""
        execution = Execution.create()

        scenario = Scenario.create("Test Login", "Authentication")
        scenario.start()

        step = Step.create("I am on login page", "Given")
        step.start()
        step.complete_successfully()
        scenario.add_step(step)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        return execution

    def test_start_execution_prints_message(self, reporter, sample_execution, capsys):
        """Test that execution start is printed"""
        reporter.start_execution(sample_execution)

        captured = capsys.readouterr()
        # ConsoleReporter uses Rich formatting, check for framework name
        assert "NEMESIS" in captured.out or "Test Automation" in captured.out

    def test_end_execution_prints_summary(self, reporter, sample_execution, capsys):
        """Test that execution end prints summary"""
        reporter.end_execution(sample_execution)

        captured = capsys.readouterr()
        # ConsoleReporter uses Rich formatting, check for passing
        assert "passing" in captured.out or "passed" in captured.out.lower()

    def test_start_scenario_prints_message(self, reporter, capsys):
        """Test that scenario start is printed"""
        scenario = Scenario.create("Test Login", "Authentication")
        reporter.start_scenario(scenario)

        captured = capsys.readouterr()
        # ConsoleReporter prints feature name
        assert "Authentication" in captured.out

    def test_end_scenario_with_success(self, reporter, capsys):
        """Test scenario end with success"""
        scenario = Scenario.create("Test", "Feature")
        scenario.start()

        step = Step.create("Test step", "Given")
        step.start()
        step.complete_successfully()
        scenario.add_step(step)

        scenario.complete()
        reporter.end_scenario(scenario)

        captured = capsys.readouterr()
        assert "✓" in captured.out or "PASSED" in captured.out

    def test_end_scenario_with_failure(self, reporter, capsys):
        """Test scenario end with failure"""
        scenario = Scenario.create("Test", "Feature")
        scenario.start()

        step = Step.create("Test step", "Given")
        step.start()
        step.fail("Error")
        scenario.add_step(step)

        scenario.complete()
        reporter.end_scenario(scenario)

        captured = capsys.readouterr()
        assert "✗" in captured.out or "FAILED" in captured.out

    def test_generate_report_returns_none(self, reporter, sample_execution):
        """Test that generate_report returns None (console only)"""
        report_path = reporter.generate_report(sample_execution, Path("/tmp"))
        assert report_path is None

    def test_attach_file(self, reporter):
        """Test attaching file (no-op for console reporter)"""
        reporter.attach_file(Path("/tmp/test.png"))
        # No exception should be raised

    def test_log_message(self, reporter):
        """Test logging message (no-op for console reporter)"""
        reporter.log_message("Test message", level="INFO")
        # No exception should be raised

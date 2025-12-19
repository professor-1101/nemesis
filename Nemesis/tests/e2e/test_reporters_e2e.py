"""E2E tests for reporter implementations"""

import pytest
from pathlib import Path
import json

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.infrastructure import JSONReporter, ConsoleReporter


class TestJSONReporterE2E:
    """End-to-end tests for JSONReporter"""

    def test_complete_execution_lifecycle(self, tmp_path):
        """Test complete execution reporting lifecycle"""
        # Setup
        reporter = JSONReporter(output_dir=tmp_path)

        # Create test data
        execution = Execution.create()
        scenario = Scenario.create(name="Login Test", feature_name="Authentication")
        scenario.start()

        step1 = Step.create(keyword="Given", name="I am on login page")
        step1.start()
        step1.complete_successfully()
        scenario.add_step(step1)

        step2 = Step.create(keyword="When", name="I enter credentials")
        step2.start()
        step2.complete_successfully()
        scenario.add_step(step2)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        # Execute lifecycle
        reporter.start_execution(execution)
        reporter.start_scenario(scenario)
        reporter.start_step(step1)
        reporter.end_step(step1)
        reporter.start_step(step2)
        reporter.end_step(step2)
        reporter.end_scenario(scenario)
        reporter.end_execution(execution)

        # Generate report
        report_path = reporter.generate_report(execution, tmp_path)

        # Verify
        assert report_path is not None
        assert report_path.exists()

        # Verify report content
        with open(report_path) as f:
            data = json.load(f)

        assert data["total_scenarios"] == 1
        assert data["passed_scenarios"] == 1
        assert data["failed_scenarios"] == 0
        assert data["is_successful"] is True
        assert len(data["scenarios"]) == 1
        assert data["scenarios"][0]["name"] == "Login Test"

    def test_failed_scenario_reporting(self, tmp_path):
        """Test reporting of failed scenarios"""
        reporter = JSONReporter(output_dir=tmp_path)

        execution = Execution.create()
        scenario = Scenario.create(name="Failed Test", feature_name="Test")
        scenario.start()

        step = Step.create(keyword="When", name="something fails")
        step.start()
        step.fail("Assertion failed")
        scenario.add_step(step)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        reporter.start_execution(execution)
        reporter.start_scenario(scenario)
        reporter.start_step(step)
        reporter.end_step(step)
        reporter.end_scenario(scenario)
        reporter.end_execution(execution)

        report_path = reporter.generate_report(execution, tmp_path)

        with open(report_path) as f:
            data = json.load(f)

        assert data["failed_scenarios"] == 1
        assert data["is_successful"] is False

    def test_multiple_scenarios(self, tmp_path):
        """Test reporting multiple scenarios"""
        reporter = JSONReporter(output_dir=tmp_path)

        execution = Execution.create()

        # Scenario 1: Pass
        s1 = Scenario.create(name="Test 1", feature_name="Feature")
        s1.start()
        step1 = Step.create(keyword="Given", name="step 1")
        step1.start()
        step1.complete_successfully()
        s1.add_step(step1)
        s1.complete()
        execution.add_scenario(s1)

        # Scenario 2: Fail
        s2 = Scenario.create(name="Test 2", feature_name="Feature")
        s2.start()
        step2 = Step.create(keyword="Given", name="step 2")
        step2.start()
        step2.fail("error")
        s2.add_step(step2)
        s2.complete()
        execution.add_scenario(s2)

        # Scenario 3: Pass
        s3 = Scenario.create(name="Test 3", feature_name="Feature")
        s3.start()
        step3 = Step.create(keyword="Given", name="step 3")
        step3.start()
        step3.complete_successfully()
        s3.add_step(step3)
        s3.complete()
        execution.add_scenario(s3)

        execution.complete()

        # Report all
        reporter.start_execution(execution)
        for s in [s1, s2, s3]:
            reporter.start_scenario(s)
            for step in s.steps:
                reporter.start_step(step)
                reporter.end_step(step)
            reporter.end_scenario(s)
        reporter.end_execution(execution)

        report_path = reporter.generate_report(execution, tmp_path)

        with open(report_path) as f:
            data = json.load(f)

        assert data["total_scenarios"] == 3
        assert data["passed_scenarios"] == 2
        assert data["failed_scenarios"] == 1


class TestConsoleReporterE2E:
    """End-to-end tests for ConsoleReporter"""

    def test_console_reporter_lifecycle(self, capsys):
        """Test ConsoleReporter outputs correctly"""
        reporter = ConsoleReporter()

        execution = Execution.create()
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        step = Step.create(keyword="Given", name="test step")
        step.start()
        step.complete_successfully()
        scenario.add_step(step)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        # Execute lifecycle
        reporter.start_execution(execution)
        reporter.start_scenario(scenario)
        reporter.start_step(step)
        reporter.end_step(step)
        reporter.end_scenario(scenario)
        reporter.end_execution(execution)

        # Verify output was produced (ConsoleReporter prints to stdout)
        captured = capsys.readouterr()
        # Basic check that something was printed
        assert len(captured.out) > 0 or len(captured.err) > 0

    def test_console_reporter_with_failure(self, capsys):
        """Test ConsoleReporter with failed step"""
        reporter = ConsoleReporter()

        execution = Execution.create()
        scenario = Scenario.create(name="Failed Test", feature_name="Feature")
        scenario.start()

        step = Step.create(keyword="When", name="this fails")
        step.start()
        step.fail("Test error")
        scenario.add_step(step)

        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        reporter.start_execution(execution)
        reporter.start_scenario(scenario)
        reporter.start_step(step)
        reporter.end_step(step)
        reporter.end_scenario(scenario)
        reporter.end_execution(execution)

        # Verify output
        captured = capsys.readouterr()
        assert len(captured.out) > 0 or len(captured.err) > 0

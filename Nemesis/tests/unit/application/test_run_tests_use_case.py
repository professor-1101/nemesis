"""Unit tests for RunTestsUseCase"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from nemesis.application.use_cases.run_tests import RunTestsUseCase, RunTestsConfig
from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import ScenarioStatus, StepStatus


class TestRunTestsConfig:
    """Tests for RunTestsConfig value object"""

    def test_create_valid_config(self):
        """Test creating valid configuration"""
        config = RunTestsConfig(
            tags=["@smoke"],
            feature="login.feature",
            env="dev",
            headless=True,
            parallel=1,
            browser_type="chromium"
        )

        assert config.tags == ["@smoke"]
        assert config.feature == "login.feature"
        assert config.env == "dev"
        assert config.headless is True
        assert config.parallel == 1
        assert config.browser_type == "chromium"

    def test_config_to_dict(self):
        """Test converting config to dictionary"""
        config = RunTestsConfig(
            tags=["@smoke"],
            feature=None,
            env="prod",
            headless=False,
            parallel=4
        )

        config_dict = config.to_dict()

        assert config_dict["tags"] == ["@smoke"]
        assert config_dict["feature"] is None
        assert config_dict["env"] == "prod"
        assert config_dict["headless"] is False
        assert config_dict["parallel"] == 4

    def test_default_values(self):
        """Test default configuration values"""
        config = RunTestsConfig(
            tags=[],
            feature=None,
            env="dev",
            headless=True,
            parallel=1
        )

        assert config.browser_type == "chromium"
        assert config.timeout == 30000
        assert config.video_enabled is True
        assert config.trace_enabled is True
        assert config.screenshot_on_failure is True


class TestRunTestsUseCase:
    """Tests for RunTestsUseCase"""

    @pytest.fixture
    def mock_browser_driver(self):
        """Create mock browser driver"""
        driver = Mock()
        driver.is_running.return_value = True
        driver._browser = None
        return driver

    @pytest.fixture
    def mock_reporter(self):
        """Create mock reporter"""
        reporter = Mock()
        reporter.generate_report.return_value = Path("/tmp/report.json")
        return reporter

    @pytest.fixture
    def mock_collector(self):
        """Create mock collector"""
        return Mock()

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory"""
        return tmp_path / "output"

    @pytest.fixture
    def use_case(self, mock_browser_driver, mock_reporter, mock_collector, output_dir):
        """Create use case instance"""
        return RunTestsUseCase(
            browser_driver=mock_browser_driver,
            reporters=[mock_reporter],
            collectors=[mock_collector],
            output_dir=output_dir
        )

    def test_initialization(self, use_case, output_dir):
        """Test use case initialization"""
        assert use_case.browser_driver is not None
        assert len(use_case.reporters) == 1
        assert len(use_case.collectors) == 1
        assert use_case.output_dir == output_dir
        assert output_dir.exists()

    def test_create_execution_with_metadata(self, use_case):
        """Test execution creation with metadata"""
        config = RunTestsConfig(
            tags=["@smoke", "@regression"],
            feature="login.feature",
            env="staging",
            headless=False,
            parallel=2,
            browser_type="firefox"
        )

        execution = use_case._create_execution(config)

        assert execution.execution_id is not None
        assert execution.metadata["env"] == "staging"
        assert execution.metadata["browser"] == "firefox"
        assert execution.metadata["headless"] == "False"
        assert execution.metadata["parallel"] == "2"
        assert execution.metadata["tags"] == "@smoke,@regression"
        assert execution.metadata["feature"] == "login.feature"

    def test_execute_with_successful_scenario(self, use_case, mock_reporter):
        """Test executing tests with successful scenario"""
        config = RunTestsConfig(
            tags=[],
            feature=None,
            env="dev",
            headless=True,
            parallel=1
        )

        # Create test scenario
        test_scenario = Scenario.create("Test Login", "Login Feature")
        step1 = Step.create("I am on login page", "Given")
        step2 = Step.create("I enter credentials", "When")
        test_scenario.steps = [step1, step2]

        # Mock scenario loader
        def scenario_loader(cfg):
            return [test_scenario]

        # Mock step executor
        def step_executor(step, scenario, cfg):
            pass  # Steps succeed by default

        # Execute
        execution = use_case.execute(config, scenario_loader, step_executor)

        # Verify
        assert execution.is_completed()
        assert execution.is_successful()
        assert execution.get_total_scenarios_count() == 1
        assert execution.get_passed_scenarios_count() == 1

        # Verify reporter was called
        mock_reporter.start_execution.assert_called_once()
        mock_reporter.end_execution.assert_called_once()
        mock_reporter.generate_report.assert_called_once()

    def test_execute_with_failing_scenario(self, use_case, mock_reporter, mock_browser_driver):
        """Test executing tests with failing scenario"""
        config = RunTestsConfig(
            tags=[],
            feature=None,
            env="dev",
            headless=True,
            parallel=1,
            screenshot_on_failure=False  # Disable to simplify test
        )

        # Create test scenario
        test_scenario = Scenario.create("Test Login", "Login Feature")
        step1 = Step.create("I am on login page", "Given")
        test_scenario.steps = [step1]

        # Mock scenario loader
        def scenario_loader(cfg):
            return [test_scenario]

        # Mock step executor that raises error
        def step_executor(step, scenario, cfg):
            raise AssertionError("Login failed")

        # Execute
        execution = use_case.execute(config, scenario_loader, step_executor)

        # Verify
        assert execution.is_completed()
        assert not execution.is_successful()
        assert execution.get_failed_scenarios_count() == 1

    def test_get_progress(self, use_case):
        """Test getting execution progress"""
        use_case._total_scenarios = 5
        use_case._completed_scenarios = 3
        use_case._current_execution = Execution.create()

        progress = use_case.get_progress()

        assert progress["total_scenarios"] == 5
        assert progress["completed_scenarios"] == 3
        assert progress["current_execution"] is not None

    def test_capture_screenshot_not_implemented_gracefully(self, use_case):
        """Test that screenshot capture handles errors gracefully"""
        scenario = Scenario.create("Test", "Feature")
        step = Step.create("Test step", "Given")

        # Should not raise exception even if browser driver is not properly set up
        use_case._capture_screenshot(step, scenario)

        # No assertion needed - just verify it doesn't crash

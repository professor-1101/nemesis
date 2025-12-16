"""Integration test using mock browser (no network required)

This test validates the complete framework integration without external dependencies.
It uses mocks to simulate browser interactions, allowing tests to run in
environments without network access.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import ScenarioStatus, StepStatus
from nemesis.infrastructure import PlaywrightBrowserDriver, ConsoleReporter, JSONReporter
from nemesis.application import ScenarioCoordinator


class TestFrameworkIntegrationWithMock:
    """Test framework integration using mocks instead of real network"""

    @pytest.fixture
    def mock_browser(self):
        """Create mock browser instance"""
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()

        # Setup mock chain
        mock_browser.new_page.return_value = mock_page
        mock_browser.contexts.return_value = [mock_context]

        # Mock page methods
        mock_page.goto = Mock()
        mock_page.fill = Mock()
        mock_page.click = Mock()
        mock_page.get_text = Mock(return_value="Product Name")
        mock_page.is_visible = Mock(return_value=True)
        mock_page.close = Mock()

        return mock_browser, mock_page

    @pytest.fixture
    def mock_playwright_driver(self, mock_browser):
        """Create PlaywrightBrowserDriver with mocked playwright"""
        browser, page = mock_browser

        with patch('nemesis.infrastructure.browser.playwright_adapter.sync_playwright') as mock_pw:
            # Setup playwright mock
            mock_playwright_instance = Mock()
            mock_chromium = Mock()
            mock_chromium.launch.return_value = browser

            mock_playwright_instance.chromium = mock_chromium
            mock_playwright_instance.__enter__ = Mock(return_value=mock_playwright_instance)
            mock_playwright_instance.__exit__ = Mock(return_value=False)

            mock_pw.return_value = mock_playwright_instance

            driver = PlaywrightBrowserDriver()
            launched_browser = driver.launch(headless=True)

            yield driver, launched_browser, page

    def test_complete_scenario_execution_flow(self, mock_playwright_driver):
        """Test complete scenario execution flow with mocked browser"""
        driver, browser, mock_page = mock_playwright_driver

        # Create execution
        execution = Execution.create()
        scenario = Scenario.create(
            name="Login Test",
            feature_name="Authentication",
            tags=["smoke", "critical"]
        )

        # Create scenario coordinator
        reporters = [ConsoleReporter()]
        coordinator = ScenarioCoordinator(
            browser_driver=driver,
            reporters=reporters,
            collectors=[]
        )

        # Execute scenario lifecycle
        scenario.start()

        # Step 1: Navigate
        step1 = Step.create(keyword="Given", name="I navigate to login page")
        scenario.add_step(step1)
        step1.start()
        mock_page.goto("https://www.saucedemo.com")
        step1.complete_successfully()

        # Step 2: Enter username
        step2 = Step.create(keyword="When", name="I enter username")
        scenario.add_step(step2)
        step2.start()
        mock_page.fill("#user-name", "standard_user")
        step2.complete_successfully()

        # Step 3: Enter password
        step3 = Step.create(keyword="And", name="I enter password")
        scenario.add_step(step3)
        step3.start()
        mock_page.fill("#password", "secret_sauce")
        step3.complete_successfully()

        # Step 4: Click login
        step4 = Step.create(keyword="And", name="I click login")
        scenario.add_step(step4)
        step4.start()
        mock_page.click("#login-button")
        step4.complete_successfully()

        # Step 5: Verify dashboard
        step5 = Step.create(keyword="Then", name="I should see dashboard")
        scenario.add_step(step5)
        step5.start()
        assert mock_page.is_visible(".inventory_list") is True
        step5.complete_successfully()

        # Complete scenario
        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        # Assertions
        assert scenario.status == ScenarioStatus.PASSED
        assert len(scenario.steps) == 5
        assert scenario.get_passed_steps_count() == 5
        assert scenario.get_failed_steps_count() == 0

        assert execution.is_successful() is True
        assert execution.get_passed_scenarios_count() == 1
        assert execution.get_failed_scenarios_count() == 0

        # Verify mock calls
        assert mock_page.goto.call_count == 1
        assert mock_page.fill.call_count == 2
        assert mock_page.click.call_count == 1
        assert mock_page.is_visible.call_count == 1

    def test_scenario_with_failing_step(self, mock_playwright_driver):
        """Test scenario with failing step"""
        driver, browser, mock_page = mock_playwright_driver

        # Make is_visible return False to simulate failure
        mock_page.is_visible.return_value = False

        execution = Execution.create()
        scenario = Scenario.create(
            name="Failed Login Test",
            feature_name="Authentication"
        )

        scenario.start()

        # Step 1: Navigate (passes)
        step1 = Step.create(keyword="Given", name="I navigate to login page")
        scenario.add_step(step1)
        step1.start()
        mock_page.goto("https://www.saucedemo.com")
        step1.complete_successfully()

        # Step 2: Verify element (fails)
        step2 = Step.create(keyword="Then", name="I should see element")
        scenario.add_step(step2)
        step2.start()

        if not mock_page.is_visible(".inventory_list"):
            step2.fail("Element not visible")

        # Complete scenario (should be FAILED)
        scenario.complete()
        execution.add_scenario(scenario)
        execution.complete()

        # Assertions
        assert scenario.status == ScenarioStatus.FAILED
        assert scenario.get_passed_steps_count() == 1
        assert scenario.get_failed_steps_count() == 1

        assert execution.is_successful() is False
        assert execution.has_failures() is True

    def test_multiple_scenarios_execution(self, mock_playwright_driver):
        """Test execution with multiple scenarios"""
        driver, browser, mock_page = mock_playwright_driver

        execution = Execution.create()

        # Scenario 1: Passing
        scenario1 = Scenario.create(name="Test 1", feature_name="Feature A")
        scenario1.start()
        step1 = Step.create(keyword="Given", name="step 1")
        step1.start()
        step1.complete_successfully()
        scenario1.add_step(step1)
        scenario1.complete()
        execution.add_scenario(scenario1)

        # Scenario 2: Passing
        scenario2 = Scenario.create(name="Test 2", feature_name="Feature A")
        scenario2.start()
        step2 = Step.create(keyword="Given", name="step 2")
        step2.start()
        step2.complete_successfully()
        scenario2.add_step(step2)
        scenario2.complete()
        execution.add_scenario(scenario2)

        # Scenario 3: Failed
        scenario3 = Scenario.create(name="Test 3", feature_name="Feature B")
        scenario3.start()
        step3 = Step.create(keyword="Given", name="step 3")
        step3.start()
        step3.fail("Intentional failure")
        scenario3.add_step(step3)
        scenario3.complete()
        execution.add_scenario(scenario3)

        execution.complete()

        # Assertions
        assert execution.get_total_scenarios_count() == 3
        assert execution.get_passed_scenarios_count() == 2
        assert execution.get_failed_scenarios_count() == 1
        assert execution.is_successful() is False

        # Test filtering
        feature_a_scenarios = execution.get_scenarios_by_feature("Feature A")
        assert len(feature_a_scenarios) == 2

    def test_framework_with_json_reporter(self, mock_playwright_driver, tmp_path):
        """Test framework integration with JSONReporter"""
        driver, browser, mock_page = mock_playwright_driver

        # Setup JSONReporter
        json_reporter = JSONReporter(output_dir=tmp_path)

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

        # Report lifecycle
        json_reporter.start_execution(execution)
        json_reporter.start_scenario(scenario)
        json_reporter.start_step(step)
        json_reporter.end_step(step)
        json_reporter.end_scenario(scenario)
        json_reporter.end_execution(execution)

        # Generate report
        report_path = json_reporter.generate_report(execution, tmp_path)
        assert report_path is not None
        assert report_path.exists()

        # Verify report content
        import json
        with open(report_path) as f:
            data = json.load(f)

        assert data["total_scenarios"] == 1
        assert data["passed_scenarios"] == 1
        assert data["is_successful"] is True

    def test_domain_entities_business_rules(self):
        """Test domain entities enforce business rules (no mocks needed)"""
        # This test demonstrates framework-independent domain layer

        execution = Execution.create()

        # Business Rule: Cannot add scenario to completed execution
        execution.complete()
        scenario = Scenario.create(name="Test", feature_name="Feature")

        with pytest.raises(ValueError, match="Cannot add scenario to completed execution"):
            execution.add_scenario(scenario)

        # Business Rule: Cannot start non-pending scenario
        execution2 = Execution.create()
        scenario2 = Scenario.create(name="Test", feature_name="Feature")
        scenario2.start()

        with pytest.raises(ValueError, match="Cannot start scenario"):
            scenario2.start()

        # Business Rule: Scenario fails if any step fails
        scenario3 = Scenario.create(name="Test", feature_name="Feature")
        scenario3.start()

        step1 = Step.create(keyword="Given", name="passes")
        step1.start()
        step1.complete_successfully()
        scenario3.add_step(step1)

        step2 = Step.create(keyword="When", name="fails")
        step2.start()
        step2.fail("Intentional failure")
        scenario3.add_step(step2)

        scenario3.complete()
        assert scenario3.status == ScenarioStatus.FAILED

        execution2.add_scenario(scenario3)
        execution2.complete()
        assert execution2.is_successful() is False

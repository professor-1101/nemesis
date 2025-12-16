"""Unit tests for Domain Layer - Entities

These tests verify business logic in domain entities.
Following DDD and Clean Architecture principles:
- Rich domain model with behavior
- Business rules encapsulated in entities
- No infrastructure dependencies
"""

import pytest
from datetime import datetime, timezone

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import ExecutionId, ScenarioStatus, StepStatus


class TestStep:
    """Test Step Entity

    Business Rules:
    - Step must have keyword and name
    - Status transitions: PENDING -> RUNNING -> (PASSED|FAILED)
    - Cannot start if not pending
    - Cannot complete if not running
    """

    def test_create_step(self):
        """GIVEN keyword and name
        WHEN creating step
        THEN should create with PENDING status"""
        # Act
        step = Step.create(keyword="Given", name="I am on login page")

        # Assert
        assert step.keyword == "Given"
        assert step.name == "I am on login page"
        assert step.status == StepStatus.PENDING
        assert step.start_time is None
        assert step.end_time is None

    def test_start_step(self):
        """GIVEN pending step
        WHEN starting step
        THEN should transition to RUNNING and set start_time"""
        # Arrange
        step = Step.create(keyword="When", name="I click login")

        # Act
        step.start()

        # Assert
        assert step.status == StepStatus.RUNNING
        assert step.start_time is not None
        assert step.end_time is None

    def test_complete_step(self):
        """GIVEN running step
        WHEN completing step
        THEN should transition to PASSED and set end_time"""
        # Arrange
        step = Step.create(keyword="Then", name="I should see dashboard")
        step.start()

        # Act
        step.complete_successfully()

        # Assert
        assert step.status == StepStatus.PASSED
        assert step.start_time is not None
        assert step.end_time is not None

    def test_fail_step(self):
        """GIVEN running step
        WHEN failing step with error message
        THEN should transition to FAILED and store error"""
        # Arrange
        step = Step.create(keyword="Then", name="I should see error")
        step.start()
        error_message = "Element not found: #error-message"

        # Act
        step.fail(error_message)

        # Assert
        assert step.status == StepStatus.FAILED
        assert step.error_message == error_message
        assert step.end_time is not None

    def test_cannot_start_non_pending_step(self):
        """GIVEN running step
        WHEN trying to start again
        THEN should raise ValueError"""
        # Arrange
        step = Step.create(keyword="Given", name="test")
        step.start()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot start step in status"):
            step.start()

    def test_cannot_complete_non_running_step(self):
        """GIVEN pending step
        WHEN trying to complete
        THEN should raise ValueError"""
        # Arrange
        step = Step.create(keyword="Given", name="test")

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot complete step in status"):
            step.complete_successfully()

    def test_is_successful_for_passed_step(self):
        """GIVEN passed step
        WHEN checking is_successful
        THEN should return True"""
        # Arrange
        step = Step.create(keyword="Given", name="test")
        step.start()
        step.complete_successfully()

        # Act
        result = step.is_successful()

        # Assert
        assert result is True

    def test_is_not_successful_for_failed_step(self):
        """GIVEN failed step
        WHEN checking is_successful
        THEN should return False"""
        # Arrange
        step = Step.create(keyword="Given", name="test")
        step.start()
        step.fail("error")

        # Act
        result = step.is_successful()

        # Assert
        assert result is False

    def test_get_duration(self):
        """GIVEN completed step
        WHEN getting duration
        THEN should return Duration object"""
        # Arrange
        step = Step.create(keyword="Given", name="test")
        step.start()
        step.complete_successfully()

        # Act
        duration = step.get_duration()

        # Assert
        assert duration is not None
        from nemesis.domain.value_objects import Duration
        assert isinstance(duration, Duration)
        assert duration.seconds >= 0


class TestScenario:
    """Test Scenario Entity

    Business Rules:
    - Scenario contains multiple steps
    - Status derived from step statuses
    - If any step fails, scenario fails
    - Cannot start if not pending
    """

    def test_create_scenario(self):
        """GIVEN name and feature
        WHEN creating scenario
        THEN should create with PENDING status"""
        # Act
        scenario = Scenario.create(
            name="Successful login",
            feature_name="Authentication"
        )

        # Assert
        assert scenario.name == "Successful login"
        assert scenario.feature_name == "Authentication"
        assert scenario.status == ScenarioStatus.PENDING
        assert len(scenario.steps) == 0

    def test_start_scenario(self):
        """GIVEN pending scenario
        WHEN starting scenario
        THEN should transition to RUNNING"""
        # Arrange
        scenario = Scenario.create(name="Test", feature_name="Feature")

        # Act
        scenario.start()

        # Assert
        assert scenario.status == ScenarioStatus.RUNNING
        assert scenario.start_time is not None

    def test_add_step_to_scenario(self):
        """GIVEN scenario and step
        WHEN adding step
        THEN step should be in scenario.steps"""
        # Arrange
        scenario = Scenario.create(name="Test", feature_name="Feature")
        step = Step.create(keyword="Given", name="test step")

        # Act
        scenario.add_step(step)

        # Assert
        assert len(scenario.steps) == 1
        assert scenario.steps[0] == step

    def test_scenario_passes_when_all_steps_pass(self):
        """GIVEN scenario with all passing steps
        WHEN completing scenario
        THEN scenario should be PASSED"""
        # Arrange
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        step1 = Step.create(keyword="Given", name="step 1")
        step1.start()
        step1.complete_successfully()
        scenario.add_step(step1)

        step2 = Step.create(keyword="When", name="step 2")
        step2.start()
        step2.complete_successfully()
        scenario.add_step(step2)

        # Act
        scenario.complete()

        # Assert
        assert scenario.status == ScenarioStatus.PASSED

    def test_scenario_fails_when_any_step_fails(self):
        """GIVEN scenario with one failing step
        WHEN completing scenario
        THEN scenario should be FAILED"""
        # Arrange
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        step1 = Step.create(keyword="Given", name="step 1")
        step1.start()
        step1.complete_successfully()
        scenario.add_step(step1)

        step2 = Step.create(keyword="When", name="step 2")
        step2.start()
        step2.fail("Something went wrong")  # This step fails
        scenario.add_step(step2)

        # Act
        scenario.complete()

        # Assert
        assert scenario.status == ScenarioStatus.FAILED

    def test_fail_scenario_directly(self):
        """GIVEN running scenario
        WHEN calling fail()
        THEN scenario should be FAILED"""
        # Arrange
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        # Act
        scenario.fail("Test failed")

        # Assert
        assert scenario.status == ScenarioStatus.FAILED
        assert scenario.end_time is not None

    def test_is_successful_for_passed_scenario(self):
        """GIVEN passed scenario
        WHEN checking is_successful
        THEN should return True"""
        # Arrange
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()

        # Act
        result = scenario.is_successful()

        # Assert
        assert result is True


class TestExecution:
    """Test Execution Entity (Aggregate Root)

    Business Rules:
    - Execution contains multiple scenarios
    - Provides statistics (total, passed, failed)
    - Cannot be completed if not running
    """

    def test_create_execution(self):
        """GIVEN no parameters
        WHEN creating execution
        THEN should generate execution_id automatically"""
        # Act
        execution = Execution.create()

        # Assert
        assert execution.execution_id is not None
        assert execution.execution_id.value.startswith("exec_")
        assert len(execution.scenarios) == 0

    def test_create_execution_with_custom_id(self):
        """GIVEN custom execution_id
        WHEN creating execution
        THEN should use provided id"""
        # Arrange
        custom_id = ExecutionId("exec_20251216_120000")

        # Act
        execution = Execution.create(execution_id=custom_id)

        # Assert
        assert execution.execution_id == custom_id

    def test_add_scenario_to_execution(self):
        """GIVEN execution and scenario
        WHEN adding scenario
        THEN scenario should be in execution.scenarios"""
        # Arrange
        execution = Execution.create()
        scenario = Scenario.create(name="Test", feature_name="Feature")

        # Act
        execution.add_scenario(scenario)

        # Assert
        assert len(execution.scenarios) == 1
        assert execution.scenarios[0] == scenario

    def test_get_total_scenarios_count(self):
        """GIVEN execution with 3 scenarios
        WHEN getting total count
        THEN should return 3"""
        # Arrange
        execution = Execution.create()
        execution.add_scenario(Scenario.create(name="S1", feature_name="F1"))
        execution.add_scenario(Scenario.create(name="S2", feature_name="F1"))
        execution.add_scenario(Scenario.create(name="S3", feature_name="F1"))

        # Act
        count = execution.get_total_scenarios_count()

        # Assert
        assert count == 3

    def test_get_passed_scenarios_count(self):
        """GIVEN execution with 2 passed and 1 failed scenario
        WHEN getting passed count
        THEN should return 2"""
        # Arrange
        execution = Execution.create()

        # Passed scenario 1
        s1 = Scenario.create(name="S1", feature_name="F1")
        s1.start()
        s1.complete()
        execution.add_scenario(s1)

        # Passed scenario 2
        s2 = Scenario.create(name="S2", feature_name="F1")
        s2.start()
        s2.complete()
        execution.add_scenario(s2)

        # Failed scenario
        s3 = Scenario.create(name="S3", feature_name="F1")
        s3.start()
        s3.fail("error")
        execution.add_scenario(s3)

        # Act
        count = execution.get_passed_scenarios_count()

        # Assert
        assert count == 2

    def test_get_failed_scenarios_count(self):
        """GIVEN execution with 2 passed and 1 failed scenario
        WHEN getting failed count
        THEN should return 1"""
        # Arrange
        execution = Execution.create()

        # Passed scenarios
        s1 = Scenario.create(name="S1", feature_name="F1")
        s1.start()
        s1.complete()
        execution.add_scenario(s1)

        s2 = Scenario.create(name="S2", feature_name="F1")
        s2.start()
        s2.complete()
        execution.add_scenario(s2)

        # Failed scenario
        s3 = Scenario.create(name="S3", feature_name="F1")
        s3.start()
        s3.fail("error")
        execution.add_scenario(s3)

        # Act
        count = execution.get_failed_scenarios_count()

        # Assert
        assert count == 1

    def test_complete_execution(self):
        """GIVEN running execution
        WHEN completing
        THEN should set end_time"""
        # Arrange
        execution = Execution.create()
        execution.start_time = datetime.now(timezone.utc)

        # Act
        execution.complete()

        # Assert
        assert execution.end_time is not None

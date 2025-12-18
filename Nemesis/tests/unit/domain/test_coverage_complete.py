"""Additional tests to achieve higher domain coverage

These tests cover remaining untested methods and edge cases.
"""

import pytest
from datetime import datetime, timezone

from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.domain.value_objects import (
    ExecutionId,
    ScenarioStatus,
    StepStatus,
    Duration
)


# ============================================================================
# Value Objects - Additional Coverage
# ============================================================================

class TestExecutionIdComplete:
    """Additional tests for ExecutionId coverage"""

    def test_extract_timestamp(self):
        """Test timestamp extraction from ID"""
        execution_id = ExecutionId("exec_20251216_143045")
        dt = execution_id.extract_timestamp()

        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 16

    def test_from_string(self):
        """Test creating from string"""
        exec_id = ExecutionId.from_string("exec_20251216_143045")
        assert exec_id.value == "exec_20251216_143045"

    def test_empty_value_raises_error(self):
        """Test empty value validation"""
        with pytest.raises(ValueError, match="cannot be empty"):
            ExecutionId("")

    def test_hash(self):
        """Test hash for set/dict usage"""
        id1 = ExecutionId("exec_20251216_143045")
        id2 = ExecutionId("exec_20251216_143045")

        assert hash(id1) == hash(id2)
        assert len({id1, id2}) == 1  # Same hash means same in set

    def test_repr_format(self):
        """Test __repr__ returns proper format"""
        exec_id = ExecutionId("exec_20251216_143045")
        result = repr(exec_id)
        assert result == "ExecutionId('exec_20251216_143045')"


class TestScenarioStatusComplete:
    """Additional tests for ScenarioStatus coverage"""

    def test_is_successful(self):
        """Test is_successful method"""
        assert ScenarioStatus.PASSED.is_successful() is True
        assert ScenarioStatus.FAILED.is_successful() is False
        assert ScenarioStatus.PENDING.is_successful() is False

    def test_is_failed(self):
        """Test is_failed method"""
        assert ScenarioStatus.FAILED.is_failed() is True
        assert ScenarioStatus.PASSED.is_failed() is False

    def test_string_conversion(self):
        """Test string representation"""
        assert str(ScenarioStatus.PASSED) == "PASSED"
        assert str(ScenarioStatus.FAILED) == "FAILED"


class TestStepStatusComplete:
    """Additional tests for StepStatus coverage"""

    def test_is_successful(self):
        """Test is_successful method"""
        assert StepStatus.PASSED.is_successful() is True
        assert StepStatus.FAILED.is_successful() is False

    def test_is_failed(self):
        """Test is_failed method"""
        assert StepStatus.FAILED.is_failed() is True
        assert StepStatus.PASSED.is_failed() is False

    def test_undefined_status_terminal(self):
        """Test UNDEFINED is terminal"""
        assert StepStatus.UNDEFINED.is_terminal() is True

    def test_string_conversion(self):
        """Test string representation"""
        assert str(StepStatus.PASSED) == "PASSED"


class TestDurationComplete:
    """Additional tests for Duration coverage"""

    def test_from_milliseconds(self):
        """Test creating from milliseconds"""
        duration = Duration.from_milliseconds(1500)
        assert duration.seconds == 1.5

    def test_to_milliseconds(self):
        """Test converting to milliseconds"""
        duration = Duration(seconds=1.5)
        assert duration.to_milliseconds() == 1500

    def test_format_short(self):
        """Test short format"""
        duration = Duration(seconds=5.5)
        assert duration.format_short() == "5.5s"

    def test_format_human_hours(self):
        """Test human format with hours"""
        duration = Duration(seconds=3665)  # 1h 1m 5s
        result = duration.format_human()
        assert "1h" in result

    def test_zero_duration(self):
        """Test zero duration class method"""
        duration = Duration.zero()
        assert duration.seconds == 0.0

    def test_negative_raises_error(self):
        """Test negative duration validation"""
        with pytest.raises(ValueError, match="cannot be negative"):
            Duration(seconds=-1.0)

    def test_arithmetic_operations(self):
        """Test duration arithmetic"""
        d1 = Duration(seconds=1.5)
        d2 = Duration(seconds=2.5)

        # Addition
        result = d1 + d2
        assert result.seconds == 4.0

        # Comparisons
        assert d1 < d2
        assert d1 <= d2
        assert d2 > d1
        assert d2 >= d1

    def test_repr(self):
        """Test repr for debugging"""
        duration = Duration(seconds=1.5)
        assert repr(duration) == "Duration(1.5)"

    def test_str_calls_format_human(self):
        """Test __str__ returns human-readable format"""
        duration = Duration(seconds=5.5)
        result = str(duration)
        assert result == "5.5s"

    def test_format_human_exact_minutes(self):
        """Test human format with exact minutes (no seconds remainder)"""
        duration = Duration(seconds=120)  # Exactly 2 minutes
        result = duration.format_human()
        assert result == "2m"

    def test_arithmetic_type_errors(self):
        """Test type errors in arithmetic operations"""
        d = Duration(seconds=1.5)

        # Test __add__ type error
        with pytest.raises(TypeError, match="Cannot add Duration"):
            _ = d + 5

        # Test __lt__ type error
        with pytest.raises(TypeError, match="Cannot compare Duration"):
            _ = d < 5

        # Test __le__ type error
        with pytest.raises(TypeError, match="Cannot compare Duration"):
            _ = d <= 5

        # Test __gt__ type error
        with pytest.raises(TypeError, match="Cannot compare Duration"):
            _ = d > 5

        # Test __ge__ type error
        with pytest.raises(TypeError, match="Cannot compare Duration"):
            _ = d >= 5


# ============================================================================
# Entities - Additional Coverage
# ============================================================================

class TestStepComplete:
    """Additional tests for Step entity coverage"""

    def test_skip_pending_step(self):
        """Test skipping a pending step"""
        step = Step.create(keyword="Given", name="test")
        step.skip()

        assert step.status == StepStatus.SKIPPED
        assert step.end_time is not None

    def test_mark_undefined(self):
        """Test marking step as undefined"""
        step = Step.create(keyword="Given", name="test")
        step.mark_undefined()

        assert step.status == StepStatus.UNDEFINED

    def test_is_completed(self):
        """Test is_completed method"""
        step = Step.create(keyword="Given", name="test")
        step.start()

        assert step.is_completed() is False
        step.complete_successfully()
        assert step.is_completed() is True

    def test_to_dict(self):
        """Test dictionary serialization"""
        step = Step.create(keyword="Given", name="test")
        step.start()
        step.complete_successfully()

        data = step.to_dict()
        assert data["name"] == "test"
        assert data["keyword"] == "Given"
        assert data["status"] == "PASSED"

    def test_repr(self):
        """Test repr"""
        step = Step.create(keyword="Given", name="test")
        result = repr(step)
        assert "Step" in result
        assert "test" in result

    def test_fail_terminal_step_raises_error(self):
        """Test failing a step that's already in terminal status"""
        step = Step.create(keyword="Given", name="test")
        step.start()
        step.complete_successfully()  # Now in PASSED (terminal)

        with pytest.raises(ValueError, match="Cannot fail step in terminal status"):
            step.fail("error")

    def test_skip_terminal_step_raises_error(self):
        """Test skipping a step that's already in terminal status"""
        step = Step.create(keyword="Given", name="test")
        step.start()
        step.complete_successfully()  # Now in PASSED (terminal)

        with pytest.raises(ValueError, match="Cannot skip step in terminal status"):
            step.skip()

    def test_get_duration_no_times(self):
        """Test get_duration when step hasn't started"""
        step = Step.create(keyword="Given", name="test")
        duration = step.get_duration()
        assert duration.seconds == 0.0


class TestScenarioComplete:
    """Additional tests for Scenario entity coverage"""

    def test_skip_scenario(self):
        """Test skipping scenario"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.skip()

        assert scenario.status == ScenarioStatus.SKIPPED

    def test_scenario_with_no_steps(self):
        """Test completing scenario with no steps"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()

        assert scenario.status == ScenarioStatus.PASSED

    def test_scenario_with_undefined_step(self):
        """Test scenario with undefined step fails"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        step = Step.create(keyword="Given", name="undefined")
        step.mark_undefined()
        scenario.add_step(step)

        scenario.complete()
        assert scenario.status == ScenarioStatus.FAILED

    def test_step_counts(self):
        """Test step counting methods"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        step1 = Step.create(keyword="Given", name="s1")
        step1.start()
        step1.complete_successfully()
        scenario.add_step(step1)

        step2 = Step.create(keyword="When", name="s2")
        step2.start()
        step2.fail("error")
        scenario.add_step(step2)

        step3 = Step.create(keyword="Then", name="s3")
        step3.skip()
        scenario.add_step(step3)

        assert scenario.get_passed_steps_count() == 1
        assert scenario.get_failed_steps_count() == 1
        assert scenario.get_skipped_steps_count() == 1

    def test_has_tag(self):
        """Test tag checking"""
        scenario = Scenario.create(
            name="Test",
            feature_name="Feature",
            tags=["smoke", "critical"]
        )

        assert scenario.has_tag("smoke") is True
        assert scenario.has_tag("nonexistent") is False

    def test_to_dict(self):
        """Test dictionary serialization"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()

        data = scenario.to_dict()
        assert data["name"] == "Test"
        assert data["status"] == "PASSED"

    def test_repr(self):
        """Test repr"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        result = repr(scenario)
        assert "Scenario" in result

    def test_start_non_pending_raises_error(self):
        """Test starting scenario that's not in PENDING status"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()  # Now RUNNING

        with pytest.raises(ValueError, match="Cannot start scenario in status"):
            scenario.start()  # Try to start again

    def test_add_step_terminal_scenario_raises_error(self):
        """Test adding step to scenario in terminal status"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()  # Now in terminal status (PASSED)

        step = Step.create(keyword="Given", name="new step")
        with pytest.raises(ValueError, match="Cannot add step to scenario in terminal status"):
            scenario.add_step(step)

    def test_complete_non_running_raises_error(self):
        """Test completing scenario that's not RUNNING"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        # Scenario is PENDING

        with pytest.raises(ValueError, match="Cannot complete scenario in status"):
            scenario.complete()

    def test_complete_with_skipped_steps_no_failures(self):
        """Test scenario completes as SKIPPED when has skipped steps but no failures"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()

        # Add passed step
        step1 = Step.create(keyword="Given", name="s1")
        step1.start()
        step1.complete_successfully()
        scenario.add_step(step1)

        # Add skipped step
        step2 = Step.create(keyword="When", name="s2")
        step2.skip()
        scenario.add_step(step2)

        scenario.complete()
        assert scenario.status == ScenarioStatus.SKIPPED

    def test_fail_terminal_scenario_raises_error(self):
        """Test failing scenario that's already in terminal status"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()  # Now PASSED (terminal)

        with pytest.raises(ValueError, match="Cannot fail scenario in terminal status"):
            scenario.fail()

    def test_skip_terminal_scenario_raises_error(self):
        """Test skipping scenario that's already in terminal status"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()  # Now PASSED (terminal)

        with pytest.raises(ValueError, match="Cannot skip scenario in terminal status"):
            scenario.skip()

    def test_get_duration_no_times(self):
        """Test get_duration when scenario hasn't started or completed"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        duration = scenario.get_duration()
        assert duration.seconds == 0.0

    def test_is_completed_returns_terminal_status(self):
        """Test is_completed uses is_terminal"""
        scenario = Scenario.create(name="Test", feature_name="Feature")
        assert scenario.is_completed() is False

        scenario.start()
        assert scenario.is_completed() is False

        scenario.complete()
        assert scenario.is_completed() is True


class TestExecutionComplete:
    """Additional tests for Execution entity coverage"""

    def test_is_completed(self):
        """Test is_completed method"""
        execution = Execution.create()

        assert execution.is_completed() is False
        execution.complete()
        assert execution.is_completed() is True

    def test_get_duration_running(self):
        """Test duration calculation while running"""
        execution = Execution.create()
        duration = execution.get_duration()

        # Should return current duration
        assert duration.seconds >= 0

    def test_get_skipped_scenarios_count(self):
        """Test counting skipped scenarios"""
        execution = Execution.create()

        s1 = Scenario.create(name="S1", feature_name="F1")
        s1.start()
        s1.skip()
        execution.add_scenario(s1)

        s2 = Scenario.create(name="S2", feature_name="F1")
        s2.start()
        s2.complete()
        execution.add_scenario(s2)

        assert execution.get_skipped_scenarios_count() == 1

    def test_get_total_steps_count(self):
        """Test counting total steps"""
        execution = Execution.create()

        scenario = Scenario.create(name="S1", feature_name="F1")
        scenario.start()

        step1 = Step.create(keyword="Given", name="s1")
        step2 = Step.create(keyword="When", name="s2")
        scenario.add_step(step1)
        scenario.add_step(step2)

        execution.add_scenario(scenario)

        assert execution.get_total_steps_count() == 2

    def test_get_passed_failed_steps_count(self):
        """Test counting passed/failed steps"""
        execution = Execution.create()

        scenario = Scenario.create(name="S1", feature_name="F1")
        scenario.start()

        step1 = Step.create(keyword="Given", name="s1")
        step1.start()
        step1.complete_successfully()
        scenario.add_step(step1)

        step2 = Step.create(keyword="When", name="s2")
        step2.start()
        step2.fail("error")
        scenario.add_step(step2)

        execution.add_scenario(scenario)

        assert execution.get_passed_steps_count() == 1
        assert execution.get_failed_steps_count() == 1

    def test_is_successful(self):
        """Test is_successful method"""
        execution = Execution.create()

        scenario = Scenario.create(name="S1", feature_name="F1")
        scenario.start()
        scenario.complete()
        execution.add_scenario(scenario)

        # With all passed scenarios
        assert execution.is_successful() is True

        # Add a failed scenario
        scenario2 = Scenario.create(name="S2", feature_name="F1")
        scenario2.start()
        scenario2.fail()
        execution.add_scenario(scenario2)

        assert execution.is_successful() is False

    def test_to_dict(self):
        """Test dictionary serialization"""
        execution = Execution.create()

        scenario = Scenario.create(name="Test", feature_name="Feature")
        scenario.start()
        scenario.complete()
        execution.add_scenario(scenario)

        execution.complete()

        data = execution.to_dict()
        assert "execution_id" in data
        assert data["total_scenarios"] == 1

    def test_repr(self):
        """Test repr"""
        execution = Execution.create()
        result = repr(execution)
        assert "Execution" in result

    def test_add_scenario_to_completed_execution_raises_error(self):
        """Test adding scenario to completed execution raises error"""
        execution = Execution.create()
        execution.complete()  # Complete execution

        scenario = Scenario.create(name="Test", feature_name="Feature")
        with pytest.raises(ValueError, match="Cannot add scenario to completed execution"):
            execution.add_scenario(scenario)

    def test_complete_already_completed_raises_error(self):
        """Test completing already completed execution raises error"""
        execution = Execution.create()
        execution.complete()  # Complete once

        with pytest.raises(ValueError, match="Execution already completed"):
            execution.complete()  # Try to complete again

    def test_is_successful_with_no_scenarios(self):
        """Test is_successful returns True when no scenarios exist"""
        execution = Execution.create()
        # No scenarios added
        assert execution.is_successful() is True

    def test_has_failures(self):
        """Test has_failures method"""
        execution = Execution.create()

        # No failures initially
        assert execution.has_failures() is False

        # Add passing scenario
        s1 = Scenario.create(name="S1", feature_name="F1")
        s1.start()
        s1.complete()
        execution.add_scenario(s1)
        assert execution.has_failures() is False

        # Add failed scenario
        s2 = Scenario.create(name="S2", feature_name="F1")
        s2.start()
        s2.fail()
        execution.add_scenario(s2)
        assert execution.has_failures() is True

    def test_get_scenarios_by_feature(self):
        """Test filtering scenarios by feature name"""
        execution = Execution.create()

        s1 = Scenario.create(name="S1", feature_name="Login")
        s2 = Scenario.create(name="S2", feature_name="Checkout")
        s3 = Scenario.create(name="S3", feature_name="Login")

        execution.add_scenario(s1)
        execution.add_scenario(s2)
        execution.add_scenario(s3)

        login_scenarios = execution.get_scenarios_by_feature("Login")
        assert len(login_scenarios) == 2
        assert s1 in login_scenarios
        assert s3 in login_scenarios

    def test_get_scenarios_by_tag(self):
        """Test filtering scenarios by tag"""
        execution = Execution.create()

        s1 = Scenario.create(name="S1", feature_name="F1", tags=["smoke", "critical"])
        s2 = Scenario.create(name="S2", feature_name="F1", tags=["regression"])
        s3 = Scenario.create(name="S3", feature_name="F1", tags=["smoke"])

        execution.add_scenario(s1)
        execution.add_scenario(s2)
        execution.add_scenario(s3)

        smoke_scenarios = execution.get_scenarios_by_tag("smoke")
        assert len(smoke_scenarios) == 2
        assert s1 in smoke_scenarios
        assert s3 in smoke_scenarios

    def test_add_metadata(self):
        """Test adding metadata to execution"""
        execution = Execution.create()

        execution.add_metadata("browser", "chromium")
        execution.add_metadata("environment", "staging")

        assert execution.metadata["browser"] == "chromium"
        assert execution.metadata["environment"] == "staging"

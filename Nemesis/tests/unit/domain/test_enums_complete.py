"""Complete tests for Enum Value Objects to achieve 100% coverage"""

import pytest

from nemesis.domain.value_objects import ScenarioStatus, StepStatus


class TestScenarioStatusMethods:
    """Test all ScenarioStatus methods"""

    def test_is_running(self):
        """Test is_running method"""
        assert ScenarioStatus.RUNNING.is_running() is True
        assert ScenarioStatus.PASSED.is_running() is False
        assert ScenarioStatus.FAILED.is_running() is False

    def test_from_string_case_insensitive(self):
        """Test from_string handles different cases"""
        assert ScenarioStatus.from_string("PASSED") == ScenarioStatus.PASSED
        assert ScenarioStatus.from_string("passed") == ScenarioStatus.PASSED
        assert ScenarioStatus.from_string("Passed") == ScenarioStatus.PASSED

    def test_from_string_behave_mapping(self):
        """Test from_string with Behave-specific values"""
        assert ScenarioStatus.from_string("EXECUTING") == ScenarioStatus.RUNNING
        assert ScenarioStatus.from_string("UNTESTED") == ScenarioStatus.PENDING

    def test_from_string_invalid_raises_error(self):
        """Test from_string with invalid value"""
        with pytest.raises(ValueError, match="Invalid scenario status"):
            ScenarioStatus.from_string("INVALID")

    def test_terminal_statuses(self):
        """Test terminal_statuses class method"""
        terminal = ScenarioStatus.terminal_statuses()

        assert ScenarioStatus.PASSED in terminal
        assert ScenarioStatus.FAILED in terminal
        assert ScenarioStatus.SKIPPED in terminal
        assert ScenarioStatus.RUNNING not in terminal
        assert ScenarioStatus.PENDING not in terminal

    def test_repr(self):
        """Test __repr__ method"""
        result = repr(ScenarioStatus.PASSED)
        assert "ScenarioStatus" in result
        assert "PASSED" in result


class TestStepStatusMethods:
    """Test all StepStatus methods"""

    def test_from_string_case_insensitive(self):
        """Test from_string handles different cases"""
        assert StepStatus.from_string("PASSED") == StepStatus.PASSED
        assert StepStatus.from_string("passed") == StepStatus.PASSED
        assert StepStatus.from_string("Failed") == StepStatus.FAILED

    def test_from_string_behave_mapping(self):
        """Test from_string with Behave-specific values"""
        assert StepStatus.from_string("EXECUTING") == StepStatus.RUNNING
        assert StepStatus.from_string("UNTESTED") == StepStatus.PENDING

    def test_from_string_invalid_raises_error(self):
        """Test from_string with invalid value"""
        with pytest.raises(ValueError, match="Invalid step status"):
            StepStatus.from_string("INVALID")

    def test_repr(self):
        """Test __repr__ method"""
        result = repr(StepStatus.PASSED)
        assert "StepStatus" in result
        assert "PASSED" in result

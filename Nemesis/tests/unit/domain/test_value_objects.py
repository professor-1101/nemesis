"""Unit tests for Domain Layer - Value Objects

These tests are framework-independent and test pure business logic.
Following Clean Architecture principles:
- No infrastructure dependencies (no Playwright, no database, etc.)
- Fast execution
- Tests business rules and invariants
"""

import pytest
from datetime import datetime, timezone

from nemesis.domain.value_objects import ExecutionId, ScenarioStatus, StepStatus, Duration


class TestExecutionId:
    """Test ExecutionId Value Object

    Business Rules:
    - Must start with 'exec_'
    - Must follow format 'exec_YYYYMMDD_HHMMSS'
    - Immutable (frozen dataclass)
    """

    def test_valid_execution_id(self):
        """GIVEN valid execution ID string
        WHEN creating ExecutionId
        THEN should create successfully"""
        # Arrange
        valid_id = "exec_20251216_143000"

        # Act
        execution_id = ExecutionId(valid_id)

        # Assert
        assert execution_id.value == valid_id

    def test_generate_execution_id(self):
        """GIVEN no input
        WHEN generating ExecutionId
        THEN should create with correct format"""
        # Act
        execution_id = ExecutionId.generate()

        # Assert
        assert execution_id.value.startswith("exec_")
        assert len(execution_id.value) == 20  # exec_YYYYMMDD_HHMMSS

    def test_invalid_prefix_raises_error(self):
        """GIVEN invalid prefix
        WHEN creating ExecutionId
        THEN should raise ValueError"""
        # Arrange
        invalid_id = "invalid_20251216_143000"

        # Act & Assert
        with pytest.raises(ValueError, match="must start with 'exec_'"):
            ExecutionId(invalid_id)

    def test_invalid_format_raises_error(self):
        """GIVEN invalid format
        WHEN creating ExecutionId
        THEN should raise ValueError"""
        # Arrange
        invalid_id = "exec_invalid_format"

        # Act & Assert
        with pytest.raises(ValueError, match="must match format"):
            ExecutionId(invalid_id)

    def test_immutability(self):
        """GIVEN ExecutionId instance
        WHEN trying to modify value
        THEN should raise error (frozen dataclass)"""
        # Arrange
        execution_id = ExecutionId.generate()

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError
            execution_id.value = "new_value"  # type: ignore


class TestScenarioStatus:
    """Test ScenarioStatus Value Object

    Business Rules:
    - Enum with predefined statuses
    - Terminal statuses cannot transition
    """

    def test_all_statuses_exist(self):
        """GIVEN ScenarioStatus enum
        WHEN checking all statuses
        THEN should have all expected values"""
        # Assert
        assert ScenarioStatus.PENDING == "PENDING"
        assert ScenarioStatus.RUNNING == "RUNNING"
        assert ScenarioStatus.PASSED == "PASSED"
        assert ScenarioStatus.FAILED == "FAILED"
        assert ScenarioStatus.SKIPPED == "SKIPPED"

    def test_is_terminal_for_passed(self):
        """GIVEN PASSED status
        WHEN checking is_terminal
        THEN should return True"""
        # Arrange
        status = ScenarioStatus.PASSED

        # Act
        result = status.is_terminal()

        # Assert
        assert result is True

    def test_is_terminal_for_failed(self):
        """GIVEN FAILED status
        WHEN checking is_terminal
        THEN should return True"""
        # Arrange
        status = ScenarioStatus.FAILED

        # Act
        result = status.is_terminal()

        # Assert
        assert result is True

    def test_is_terminal_for_skipped(self):
        """GIVEN SKIPPED status
        WHEN checking is_terminal
        THEN should return True"""
        # Arrange
        status = ScenarioStatus.SKIPPED

        # Act
        result = status.is_terminal()

        # Assert
        assert result is True

    def test_is_not_terminal_for_pending(self):
        """GIVEN PENDING status
        WHEN checking is_terminal
        THEN should return False"""
        # Arrange
        status = ScenarioStatus.PENDING

        # Act
        result = status.is_terminal()

        # Assert
        assert result is False

    def test_is_not_terminal_for_running(self):
        """GIVEN RUNNING status
        WHEN checking is_terminal
        THEN should return False"""
        # Arrange
        status = ScenarioStatus.RUNNING

        # Act
        result = status.is_terminal()

        # Assert
        assert result is False


class TestStepStatus:
    """Test StepStatus Value Object"""

    def test_all_statuses_exist(self):
        """GIVEN StepStatus enum
        WHEN checking all statuses
        THEN should have all expected values"""
        # Assert
        assert StepStatus.PENDING == "PENDING"
        assert StepStatus.RUNNING == "RUNNING"
        assert StepStatus.PASSED == "PASSED"
        assert StepStatus.FAILED == "FAILED"
        assert StepStatus.SKIPPED == "SKIPPED"


class TestDuration:
    """Test Duration Value Object

    Business Rules:
    - Formats duration in human-readable format
    - Milliseconds for < 1s
    - Seconds for < 60s
    - Minutes and seconds for >= 60s
    """

    def test_format_milliseconds(self):
        """GIVEN duration < 1 second
        WHEN formatting
        THEN should show milliseconds"""
        # Arrange
        duration = Duration(seconds=0.5)

        # Act
        formatted = duration.format_human()

        # Assert
        assert formatted == "500ms"

    def test_format_seconds(self):
        """GIVEN duration < 60 seconds
        WHEN formatting
        THEN should show seconds"""
        # Arrange
        duration = Duration(seconds=5.5)

        # Act
        formatted = duration.format_human()

        # Assert
        assert formatted == "5.5s"

    def test_format_minutes_and_seconds(self):
        """GIVEN duration >= 60 seconds
        WHEN formatting
        THEN should show minutes and seconds"""
        # Arrange
        duration = Duration(seconds=125.0)  # 2m 5s

        # Act
        formatted = duration.format_human()

        # Assert
        assert formatted == "2m 5s"

    def test_immutability(self):
        """GIVEN Duration instance
        WHEN trying to modify seconds
        THEN should raise error (frozen dataclass)"""
        # Arrange
        duration = Duration(seconds=5.0)

        # Act & Assert
        with pytest.raises(Exception):  # FrozenInstanceError
            duration.seconds = 10.0  # type: ignore

    def test_zero_duration(self):
        """GIVEN zero duration
        WHEN formatting
        THEN should show 0ms"""
        # Arrange
        duration = Duration(seconds=0.0)

        # Act
        formatted = duration.format_human()

        # Assert
        assert formatted == "0ms"

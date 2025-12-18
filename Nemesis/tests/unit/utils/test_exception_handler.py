"""Tests for exception handling decorator."""

import pytest
from unittest.mock import Mock, patch

from nemesis.utils.decorators.exception_handler import (
    handle_exceptions,
    handle_exceptions_with_fallback,
)


class TestHandleExceptions:
    """Test handle_exceptions decorator."""

    def test_successful_execution_no_exception(self):
        """Test decorator allows successful execution without exceptions."""
        mock_logger = Mock()

        @handle_exceptions(logger=mock_logger)
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"
        mock_logger.error.assert_not_called()

    def test_keyboard_interrupt_always_raised(self):
        """Test KeyboardInterrupt is always re-raised."""
        mock_logger = Mock()

        @handle_exceptions(logger=mock_logger)
        def keyboard_interrupt_func():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            keyboard_interrupt_func()

        # Should not log KeyboardInterrupt
        mock_logger.error.assert_not_called()

    def test_system_exit_always_raised(self):
        """Test SystemExit is always re-raised."""
        mock_logger = Mock()

        @handle_exceptions(logger=mock_logger)
        def system_exit_func():
            raise SystemExit()

        with pytest.raises(SystemExit):
            system_exit_func()

        # Should not log SystemExit
        mock_logger.error.assert_not_called()

    def test_catch_specific_exception_with_logging(self):
        """Test catching specific exceptions and logging."""
        mock_logger = Mock()

        @handle_exceptions(
            logger=mock_logger,
            catch_exceptions=(RuntimeError, AttributeError),
            message_template="Test error: {error}",
        )
        def failing_func():
            raise RuntimeError("test error")

        result = failing_func()

        # Should return None by default
        assert result is None

        # Should log error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Test error: test error" in call_args[0][0]
        assert "traceback" in call_args[1]

    def test_custom_default_return_value(self):
        """Test returning custom default value on exception."""
        mock_logger = Mock()

        @handle_exceptions(
            logger=mock_logger, catch_exceptions=(ValueError,), default_return=False
        )
        def failing_func():
            raise ValueError("test")

        result = failing_func()
        assert result is False

    def test_reraise_after_logging(self):
        """Test re-raising exception after logging."""
        mock_logger = Mock()

        @handle_exceptions(
            logger=mock_logger,
            catch_exceptions=(RuntimeError,),
            reraise=True,
            message_template="Error: {error}",
        )
        def failing_func():
            raise RuntimeError("test")

        with pytest.raises(RuntimeError):
            failing_func()

        # Should still log before re-raising
        mock_logger.error.assert_called_once()

    def test_different_log_levels(self):
        """Test using different log levels."""
        mock_logger = Mock()

        @handle_exceptions(
            logger=mock_logger,
            log_level="warning",
            catch_exceptions=(ValueError,),
            message_template="Warning: {error}",
        )
        def warning_func():
            raise ValueError("test")

        warning_func()
        mock_logger.warning.assert_called_once()

        mock_logger.reset_mock()

        @handle_exceptions(
            logger=mock_logger,
            log_level="critical",
            catch_exceptions=(ValueError,),
            message_template="Critical: {error}",
        )
        def critical_func():
            raise ValueError("test")

        critical_func()
        mock_logger.critical.assert_called_once()

    def test_auto_detect_class_name_from_self(self):
        """Test auto-detection of class name from self parameter."""
        mock_logger = Mock()

        class TestClass:
            @handle_exceptions(logger=mock_logger, catch_exceptions=(ValueError,))
            def method(self):
                raise ValueError("test")

        obj = TestClass()
        obj.method()

        call_args = mock_logger.error.call_args
        assert call_args[1]["class_name"] == "TestClass"
        assert call_args[1]["method"] == "method"

    def test_include_module_context(self):
        """Test including module context in logs."""
        mock_logger = Mock()

        @handle_exceptions(
            logger=mock_logger,
            catch_exceptions=(ValueError,),
            module="test_module",
        )
        def test_func():
            raise ValueError("test")

        test_func()

        call_args = mock_logger.error.call_args
        assert call_args[1]["module"] == "test_module"

    def test_disable_traceback(self):
        """Test disabling traceback in logs."""
        mock_logger = Mock()

        @handle_exceptions(
            logger=mock_logger,
            catch_exceptions=(ValueError,),
            include_traceback=False,
        )
        def test_func():
            raise ValueError("test")

        test_func()

        call_args = mock_logger.error.call_args
        assert "traceback" not in call_args[1]

    def test_auto_get_logger_from_self(self):
        """Test auto-getting logger from self if not provided."""

        class TestClass:
            def __init__(self):
                self.logger = Mock()

            @handle_exceptions(catch_exceptions=(ValueError,))
            def method(self):
                raise ValueError("test")

        obj = TestClass()
        obj.method()

        obj.logger.error.assert_called_once()

    @patch("nemesis.utils.decorators.exception_handler.Logger")
    def test_fallback_to_singleton_logger(self, mock_logger_class):
        """Test falling back to singleton logger if no logger provided."""
        mock_logger_instance = Mock()
        mock_logger_class.get_instance.return_value = mock_logger_instance

        @handle_exceptions(catch_exceptions=(ValueError,))
        def test_func():
            raise ValueError("test")

        test_func()

        mock_logger_instance.error.assert_called_once()


class TestHandleExceptionsWithFallback:
    """Test handle_exceptions_with_fallback decorator."""

    def test_specific_exception_caught(self):
        """Test specific exceptions are caught with specific message."""
        mock_logger = Mock()

        @handle_exceptions_with_fallback(
            logger=mock_logger,
            specific_exceptions=(RuntimeError, AttributeError),
            specific_message="Specific error: {error}",
            fallback_message="Unexpected error: {error}",
        )
        def test_func():
            raise RuntimeError("specific")

        test_func()

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "Specific error: specific" in call_args[0][0]

    def test_unexpected_exception_caught(self):
        """Test unexpected exceptions are caught with fallback message."""
        mock_logger = Mock()

        @handle_exceptions_with_fallback(
            logger=mock_logger,
            specific_exceptions=(RuntimeError,),
            specific_message="Specific error: {error}",
            fallback_message="Unexpected error: {error}",
        )
        def test_func():
            raise ValueError("unexpected")

        test_func()

        # Unexpected exceptions should use error level
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Unexpected error: unexpected" in call_args[0][0]

    def test_keyboard_interrupt_still_raised(self):
        """Test KeyboardInterrupt is always re-raised in fallback mode."""
        mock_logger = Mock()

        @handle_exceptions_with_fallback(
            logger=mock_logger,
            specific_exceptions=(RuntimeError,),
            specific_message="Error: {error}",
            fallback_message="Fallback: {error}",
        )
        def test_func():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            test_func()

        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()

    def test_return_value_on_any_error(self):
        """Test returning custom value on any error."""
        mock_logger = Mock()

        @handle_exceptions_with_fallback(
            logger=mock_logger,
            specific_exceptions=(RuntimeError,),
            specific_message="Error: {error}",
            fallback_message="Fallback: {error}",
            return_on_error=False,
        )
        def test_func():
            raise ValueError("test")

        result = test_func()
        assert result is False

    def test_class_method_with_fallback(self):
        """Test fallback decorator works with class methods."""
        mock_logger = Mock()

        class TestClass:
            @handle_exceptions_with_fallback(
                logger=mock_logger,
                specific_exceptions=(ValueError,),
                specific_message="Specific: {error}",
                fallback_message="Fallback: {error}",
            )
            def method(self):
                raise RuntimeError("unexpected")

        obj = TestClass()
        obj.method()

        # Should log as unexpected error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]["class_name"] == "TestClass"

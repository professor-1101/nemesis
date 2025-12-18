"""Exception handling decorator for consistent error handling across the codebase.

This decorator eliminates repetitive exception handling boilerplate by providing
a standardized way to catch, log, and handle exceptions with proper context.
"""

import functools
import traceback as tb
from typing import Any, Callable, Optional, TypeVar, Union

from nemesis.infrastructure.logging import Logger

F = TypeVar("F", bound=Callable[..., Any])


def handle_exceptions(
    *,
    logger: Optional[Logger] = None,
    log_level: str = "error",
    catch_exceptions: tuple[type[Exception], ...] = (Exception,),
    reraise: bool = False,
    default_return: Any = None,
    message_template: Optional[str] = None,
    include_traceback: bool = True,
    module: Optional[str] = None,
    class_name: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator for consistent exception handling with logging.

    Automatically handles KeyboardInterrupt and SystemExit by re-raising them.
    Catches specified exceptions, logs them with context, and optionally re-raises
    or returns a default value.

    Args:
        logger: Logger instance to use. If None, gets singleton instance.
        log_level: Logging level - "debug", "info", "warning", "error", "critical"
        catch_exceptions: Tuple of exception types to catch and handle
        reraise: Whether to re-raise the exception after logging
        default_return: Value to return if exception caught and not re-raised
        message_template: Custom message template. Use {error} placeholder for exception message
        include_traceback: Whether to include traceback in log
        module: Module name for logging context (uses __name__ if not provided)
        class_name: Class name for logging context (auto-detected from self if not provided)

    Returns:
        Decorated function with exception handling

    Example:
        ```python
        @handle_exceptions(
            logger=self.logger,
            log_level="error",
            catch_exceptions=(RuntimeError, AttributeError),
            message_template="Failed to start browser: {error}"
        )
        def start_browser(self):
            # Method implementation
            pass
        ```

    Pattern replaced:
        ```python
        # Before:
        def method(self):
            try:
                # implementation
            except (KeyboardInterrupt, SystemExit):
                raise
            except (RuntimeError, AttributeError) as e:
                self.logger.error(
                    f"Error message: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name="ClassName",
                    method="method"
                )

        # After:
        @handle_exceptions(
            logger=self.logger,
            catch_exceptions=(RuntimeError, AttributeError),
            message_template="Error message: {error}"
        )
        def method(self):
            # implementation
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger instance
            log_instance = logger
            if log_instance is None:
                # Try to get from self if method
                if args and hasattr(args[0], "logger"):
                    log_instance = args[0].logger
                else:
                    log_instance = Logger.get_instance({})

            # Determine class name
            actual_class_name = class_name
            if actual_class_name is None and args and hasattr(args[0], "__class__"):
                actual_class_name = args[0].__class__.__name__

            # Determine module name
            actual_module = module if module is not None else func.__module__

            try:
                return func(*args, **kwargs)

            except (KeyboardInterrupt, SystemExit):
                # Always re-raise these to allow proper program termination
                raise

            except catch_exceptions as e:
                # Build error message
                if message_template:
                    error_msg = message_template.format(error=str(e))
                else:
                    error_msg = f"Error in {func.__name__}: {e}"

                # Build log kwargs
                log_kwargs: dict[str, Any] = {
                    "module": actual_module,
                    "method": func.__name__,
                }

                if actual_class_name:
                    log_kwargs["class_name"] = actual_class_name

                if include_traceback:
                    log_kwargs["traceback"] = tb.format_exc()

                # Log at appropriate level
                log_method = getattr(log_instance, log_level, log_instance.error)
                log_method(error_msg, **log_kwargs)

                # Re-raise or return default
                if reraise:
                    raise
                return default_return

        return wrapper  # type: ignore

    return decorator


def handle_exceptions_with_fallback(
    *,
    logger: Optional[Logger] = None,
    log_level: str = "warning",
    specific_exceptions: tuple[type[Exception], ...] = (),
    specific_message: Optional[str] = None,
    fallback_message: Optional[str] = None,
    include_traceback: bool = True,
    module: Optional[str] = None,
    class_name: Optional[str] = None,
    return_on_error: Any = None,
) -> Callable[[F], F]:
    """
    Decorator for handling specific exceptions with a fallback for unexpected ones.

    This pattern is common in the codebase where specific exceptions are caught
    with one message, and a broad Exception catch-all is used for unexpected errors.

    Args:
        logger: Logger instance
        log_level: Log level for specific exceptions
        specific_exceptions: Tuple of specific exception types to catch first
        specific_message: Message template for specific exceptions
        fallback_message: Message template for unexpected exceptions
        include_traceback: Whether to include traceback
        module: Module name for context
        class_name: Class name for context
        return_on_error: Value to return on any error

    Returns:
        Decorated function

    Example:
        ```python
        # Before:
        def method(self):
            try:
                # implementation
            except (KeyboardInterrupt, SystemExit):
                raise
            except (AttributeError, RuntimeError) as e:
                self.logger.error(f"Specific error: {e}", traceback=traceback.format_exc())
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}", traceback=traceback.format_exc())

        # After:
        @handle_exceptions_with_fallback(
            logger=self.logger,
            specific_exceptions=(AttributeError, RuntimeError),
            specific_message="Specific error: {error}",
            fallback_message="Unexpected error: {error}"
        )
        def method(self):
            # implementation
        ```
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger instance
            log_instance = logger
            if log_instance is None:
                if args and hasattr(args[0], "logger"):
                    log_instance = args[0].logger
                else:
                    log_instance = Logger.get_instance({})

            # Determine class name
            actual_class_name = class_name
            if actual_class_name is None and args and hasattr(args[0], "__class__"):
                actual_class_name = args[0].__class__.__name__

            # Determine module name
            actual_module = module if module is not None else func.__module__

            try:
                return func(*args, **kwargs)

            except (KeyboardInterrupt, SystemExit):
                # Always re-raise
                raise

            except specific_exceptions as e:
                # Handle specific exceptions
                msg = specific_message.format(error=str(e)) if specific_message else f"Error: {e}"

                log_kwargs: dict[str, Any] = {
                    "module": actual_module,
                    "method": func.__name__,
                }
                if actual_class_name:
                    log_kwargs["class_name"] = actual_class_name
                if include_traceback:
                    log_kwargs["traceback"] = tb.format_exc()

                log_method = getattr(log_instance, log_level, log_instance.error)
                log_method(msg, **log_kwargs)

                return return_on_error

            except Exception as e:  # pylint: disable=broad-exception-caught
                # Handle unexpected exceptions
                msg = fallback_message.format(error=str(e)) if fallback_message else f"Unexpected error: {e}"

                log_kwargs: dict[str, Any] = {
                    "module": actual_module,
                    "method": func.__name__,
                }
                if actual_class_name:
                    log_kwargs["class_name"] = actual_class_name
                if include_traceback:
                    log_kwargs["traceback"] = tb.format_exc()

                # Use error level for unexpected exceptions
                log_instance.error(msg, **log_kwargs)

                return return_on_error

        return wrapper  # type: ignore

    return decorator

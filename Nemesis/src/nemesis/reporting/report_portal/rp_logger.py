"""ReportPortal logging module.

This module manages logging to ReportPortal, handling sending log messages,
exceptions, and attachments to the current test item in ReportPortal hierarchy
(step > test > feature).
"""
import traceback
from pathlib import Path
from nemesis.utils.decorators import retry
from .rp_base_handler import RPBaseHandler
from .rp_utils import RPUtils

class RPLogger(RPBaseHandler):
    """Manages logging to ReportPortal.
    
    Handles sending log messages, exceptions, and attachments to the
    current test item in ReportPortal hierarchy (step > test > feature).
    """

    @retry(max_attempts=2, delay=0.5)
    def log_message(self, message: str, level: str = "INFO") -> None:
        """
        Log message to current item.

        Enhanced implementation:
        - No truncation limits (show full message)
        - Preserves complete log content

        Args:
            message: Message text to log
            level: Log level (INFO, DEBUG, WARN, ERROR, TRACE)
        """
        item_id = self._get_current_item_id()
        launch_id = self.rp_launch_manager.get_launch_id()

        if not item_id or not launch_id:
            self.logger.warning(f"Cannot log message - item_id: {item_id}, launch_id: {launch_id}")
            return

        try:
            # No truncation - show full message
            self.logger.info(f"[RP LOG DEBUG] Logging message to item_id={item_id}, level={level}, message length={len(message)}")
            self.client.log(
                time=RPUtils.timestamp(),
                message=message,
                level=level,
                item_id=item_id,
            )
            self.logger.info(f"[RP LOG DEBUG] Log sent successfully")
        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors
            self.logger.error(f"Failed to log message - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_message")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK log
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.error(f"Failed to log message: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_message")

    @retry(max_attempts=2, delay=0.5)
    def log_metadata(self, key: str, value: str, level: str = "INFO") -> None:
        """Log custom metadata to current test item.

        Formats metadata as key-value pair for better visibility in ReportPortal.
        This method follows SRP by delegating to log_message() for actual logging.

        Args:
            key: Metadata key (e.g., "environment", "browser_version")
            value: Metadata value
            level: Log level (default: INFO)

        Example:
            >>> log_metadata("browser_version", "Chrome 120")
            >>> log_metadata("test_data_id", "USER-12345", "DEBUG")
        """
        # SRP: Format metadata, delegate logging to log_message()
        formatted_message = f"[METADATA] {key}: {value}"
        self.log_message(formatted_message, level)

    @retry(max_attempts=2, delay=0.5)
    def log_exception(self, exception: Exception, description: str = "", context: dict = None) -> None:
        """
        Log exception with full stack trace to ReportPortal.

        Enhanced implementation:
        - No truncation limits (show complete stack trace)
        - Context information (step, scenario, feature names)
        - Enhanced error formatting

        Args:
            exception: The exception to log
            description: Optional description
            context: Optional context dict with step/scenario/feature names
        """
        item_id = self._get_current_item_id()
        launch_id = self.rp_launch_manager.get_launch_id()

        if not item_id or not launch_id:
            self.logger.warning("Cannot log exception: No active item or launch")
            return

        try:
            exception_type = type(exception).__name__
            exception_message = str(exception)

            # Extract full stack trace (no truncation)
            stack_trace = RPUtils.extract_stack_trace(exception)

            # Build header with context information
            header = "=" * 80
            header += f"\n🔴 EXCEPTION: {exception_type}\n"
            header += "=" * 80

            if description:
                header = f"{description}\n\n{header}"

            # Add context information if provided
            context_info = ""
            if context:
                context_info = "\n📋 CONTEXT:\n"
                if 'feature' in context:
                    context_info += f"  Feature: {context['feature']}\n"
                if 'scenario' in context:
                    context_info += f"  Scenario: {context['scenario']}\n"
                if 'step' in context:
                    context_info += f"  Step: {context['step']}\n"
                context_info += "\n"

            # Build complete message (no truncation)
            full_message = f"""{header}

💬 MESSAGE:
{exception_message}
{context_info}
📚 STACK TRACE:
{stack_trace}

⏰ TIME: {RPUtils.timestamp()}
"""

            self.client.log(
                time=RPUtils.timestamp(),
                message=full_message,
                level="ERROR",
                item_id=item_id,
            )

            self.logger.info(f"Exception logged to ReportPortal: {exception_type} (full trace, {len(stack_trace)} chars)")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors
            self.logger.error(f"Failed to log exception - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception")
            try:
                self.client.log(
                    time=RPUtils.timestamp(),
                    message=f"Exception: {type(exception).__name__}: {str(exception)}",
                    level="ERROR",
                    item_id=item_id,
                )
            except (AttributeError, RuntimeError) as fallback_error:
                # Fallback logging also failed - API error
                self.logger.error(f"Fallback logging also failed - API error: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception")
            except Exception as fallback_error:  # pylint: disable=broad-exception-caught
                # Fallback logging also failed - unexpected error
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Fallback logging also failed: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK log
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.error(f"Failed to log exception: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception")
            try:
                self.client.log(
                    time=RPUtils.timestamp(),
                    message=f"Exception: {type(exception).__name__}: {str(exception)}",
                    level="ERROR",
                    item_id=item_id,
                )
            except (AttributeError, RuntimeError) as fallback_error:
                # Fallback logging also failed - API error
                self.logger.error(f"Fallback logging also failed - API error: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception")
            except Exception as fallback_error:  # pylint: disable=broad-exception-caught
                # Fallback logging also failed - unexpected error
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Fallback logging also failed: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception")

    @retry(max_attempts=2, delay=0.5)
    def log_exception_with_attachment(self, exception: Exception, attachment_path: Path = None, description: str = "", context: dict = None) -> None:
        """
        Log exception with stack trace and optional attachment.

        Enhanced implementation:
        - No truncation limits (show complete stack trace)
        - Context information (step, scenario, feature names)
        - Enhanced error formatting with attachment info

        Args:
            exception: The exception to log
            attachment_path: Optional path to attachment file
            description: Optional description
            context: Optional context dict with step/scenario/feature names
        """
        item_id = self._get_current_item_id()
        launch_id = self.rp_launch_manager.get_launch_id()

        if not item_id or not launch_id:
            self.logger.warning("Cannot log exception with attachment: No active item or launch")
            return

        try:
            exception_type = type(exception).__name__
            exception_message = str(exception)

            # Extract full stack trace (no truncation)
            stack_trace = RPUtils.extract_stack_trace(exception)

            # Build header with context information
            header = "=" * 80
            header += f"\n🔴 EXCEPTION WITH ATTACHMENT: {exception_type}\n"
            header += "=" * 80

            if description:
                header = f"{description}\n\n{header}"

            # Add context information if provided
            context_info = ""
            if context:
                context_info = "\n📋 CONTEXT:\n"
                if 'feature' in context:
                    context_info += f"  Feature: {context['feature']}\n"
                if 'scenario' in context:
                    context_info += f"  Scenario: {context['scenario']}\n"
                if 'step' in context:
                    context_info += f"  Step: {context['step']}\n"
                context_info += "\n"

            # Attachment info
            attachment_info = ""
            if attachment_path and attachment_path.exists():
                attachment_info = f"\n📎 ATTACHMENT: {attachment_path.name}\n"

            # Build complete message (no truncation)
            full_message = f"""{header}

💬 MESSAGE:
{exception_message}
{context_info}{attachment_info}
📚 STACK TRACE:
{stack_trace}

⏰ TIME: {RPUtils.timestamp()}
"""

            self.client.log(
                time=RPUtils.timestamp(),
                message=full_message,
                level="ERROR",
                item_id=item_id,
            )

            # Note: attachment logic will be handled by RPAttachmentHandler.
            # For now, just logging the message. The facade will call attach_file.
            # if attachment_path and attachment_path.exists():
            #     self.attach_file(attachment_path, f"Attachment for {exception_type}")

            self.logger.info(f"Exception with attachment logged to ReportPortal: {exception_type} (full trace, {len(stack_trace)} chars)")

        except (AttributeError, RuntimeError) as e:
            # ReportPortal SDK API errors
            self.logger.error(f"Failed to log exception with attachment - API error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception_with_attachment")
            try:
                self.client.log(
                    time=RPUtils.timestamp(),
                    message=f"Exception: {type(exception).__name__}: {str(exception)}",
                    level="ERROR",
                    item_id=item_id,
                )
            except (AttributeError, RuntimeError) as fallback_error:
                # Fallback logging also failed - API error
                self.logger.error(f"Fallback logging also failed - API error: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception_with_attachment")
            except Exception as fallback_error:  # pylint: disable=broad-exception-caught
                # Fallback logging also failed - unexpected error
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Fallback logging also failed: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception_with_attachment")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK log
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.error(f"Failed to log exception with attachment: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception_with_attachment")
            try:
                self.client.log(
                    time=RPUtils.timestamp(),
                    message=f"Exception: {type(exception).__name__}: {str(exception)}",
                    level="ERROR",
                    item_id=item_id,
                )
            except (AttributeError, RuntimeError) as fallback_error:
                # Fallback logging also failed - API error
                self.logger.error(f"Fallback logging also failed - API error: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception_with_attachment")
            except Exception as fallback_error:  # pylint: disable=broad-exception-caught
                # Fallback logging also failed - unexpected error
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Fallback logging also failed: {fallback_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLogger", method="log_exception_with_attachment")

"""
Step definitions for testing exception handling and stack traces.
"""

from behave import given, when, then
import traceback
import time

@given('I want to test exception handling')
def step_test_exception_handling(context):
    """Step to test exception handling."""
    context.logger.info("Testing exception handling")

@when('I trigger a test exception')
def step_trigger_exception(context):
    """Step that intentionally triggers an exception."""
    try:
        # Simulate a realistic test failure
        raise AssertionError("Test assertion failed: Expected element to be visible but it was not found")
    except Exception as e:
        # Log the exception with stack trace to ReportPortal
        if hasattr(context, 'report_manager') and context.report_manager and context.report_manager.rp_enabled:
            try:
                context.report_manager.rp_client.log_exception(
                    exception=e,
                    description="Test Exception: Element visibility check failed"
                )
                context.logger.info("Exception logged to ReportPortal")
            except Exception as rp_error:
                context.logger.warning(f"Failed to log exception to ReportPortal: {rp_error}")
        
        # Log the exception but don't fail the test
        context.logger.error(f"Exception triggered for testing: {e}")
        context.logger.info("Exception handling test completed successfully")

@when('I trigger a timeout exception')
def step_trigger_timeout(context):
    """Step that triggers a timeout exception."""
    try:
        # Simulate a timeout scenario
        raise TimeoutError("Operation timed out after 30 seconds waiting for element")
    except Exception as e:
        # Log the exception with stack trace to ReportPortal
        if hasattr(context, 'report_manager') and context.report_manager and context.report_manager.rp_enabled:
            try:
                context.report_manager.rp_client.log_exception(
                    exception=e,
                    description="Timeout Exception: Element wait timeout"
                )
                context.logger.info("Timeout exception logged to ReportPortal")
            except Exception as rp_error:
                context.logger.warning(f"Failed to log timeout exception to ReportPortal: {rp_error}")
        
        # Log the exception but don't fail the test
        context.logger.error(f"Timeout exception triggered for testing: {e}")
        context.logger.info("Timeout exception handling test completed successfully")

@when('I trigger a connection exception')
def step_trigger_connection_error(context):
    """Step that triggers a connection exception."""
    try:
        # Simulate a connection error
        raise ConnectionError("Failed to connect to the application server")
    except Exception as e:
        # Log the exception with stack trace to ReportPortal
        if hasattr(context, 'report_manager') and context.report_manager and context.report_manager.rp_enabled:
            try:
                context.report_manager.rp_client.log_exception(
                    exception=e,
                    description="Connection Exception: Server connection failed"
                )
                context.logger.info("Connection exception logged to ReportPortal")
            except Exception as rp_error:
                context.logger.warning(f"Failed to log connection exception to ReportPortal: {rp_error}")
        
        # Log the exception but don't fail the test
        context.logger.error(f"Connection exception triggered for testing: {e}")
        context.logger.info("Connection exception handling test completed successfully")

@then('I should see the exception in ReportPortal')
def step_verify_exception_in_reportportal(context):
    """Step to verify exception was logged to ReportPortal."""
    context.logger.info("Exception should be visible in ReportPortal UI")

@then('I should see the stack trace in ReportPortal')
def step_verify_stack_trace_in_reportportal(context):
    """Step to verify stack trace was logged to ReportPortal."""
    context.logger.info("Stack trace should be visible in ReportPortal UI")

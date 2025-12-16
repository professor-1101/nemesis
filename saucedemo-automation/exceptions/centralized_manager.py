"""Centralized exception manager for all exception types."""

from typing import Any, Dict, Optional
from .environment_exceptions import EnvironmentExceptionHandler
from .browser_exceptions import BrowserExceptionHandler
from .test_exceptions import TestExceptionHandler
from .validation_exceptions import ValidationExceptionHandler
from .network_exceptions import NetworkExceptionHandler


class CentralizedExceptionManager:
    """Centralized manager for all exception types."""
    
    def __init__(self, logger=None):
        """Initialize centralized exception manager."""
        self.logger = logger
        
        # Initialize all exception handlers
        self.environment_handler = EnvironmentExceptionHandler(logger)
        self.browser_handler = BrowserExceptionHandler(logger)
        self.test_handler = TestExceptionHandler(logger)
        self.validation_handler = ValidationExceptionHandler(logger)
        self.network_handler = NetworkExceptionHandler(logger)
    
    def handle_environment_exception(self, exception: Exception, context: Dict[str, Any] = None):
        """Handle environment exceptions."""
        return self.environment_handler.handle_setup_error(exception, context)
    
    def handle_browser_exception(self, exception: Exception, browser_info: Dict[str, Any] = None):
        """Handle browser exceptions."""
        return self.browser_handler.handle_browser_start_error(exception, browser_info.get('type') if browser_info else None)
    
    def handle_test_exception(self, exception: Exception, test_info: Dict[str, Any] = None):
        """Handle test exceptions."""
        return self.test_handler.handle_test_failure(exception, test_info)
    
    def handle_validation_exception(self, exception: Exception, validation_info: Dict[str, Any] = None):
        """Handle validation exceptions."""
        return self.validation_handler.handle_form_validation_error(exception, validation_info)
    
    def handle_network_exception(self, exception: Exception, network_info: Dict[str, Any] = None):
        """Handle network exceptions."""
        return self.network_handler.handle_connection_error(exception, network_info)
    
    def handle_any_exception(self, exception: Exception, context: Dict[str, Any] = None):
        """Handle any exception by categorizing it."""
        exception_name = exception.__class__.__name__.lower()
        
        if "browser" in exception_name or "webdriver" in exception_name:
            return self.handle_browser_exception(exception, context)
        elif "timeout" in exception_name or "timeout" in str(exception).lower():
            return self.handle_network_exception(exception, context)
        elif "validation" in exception_name or "assert" in exception_name:
            return self.handle_validation_exception(exception, context)
        elif "test" in exception_name or "scenario" in exception_name:
            return self.handle_test_exception(exception, context)
        else:
            return self.handle_environment_exception(exception, context)
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """Get summaries from all handlers."""
        return {
            "environment": self.environment_handler.get_summary(),
            "browser": self.browser_handler.get_summary(),
            "test": self.test_handler.get_summary(),
            "validation": self.validation_handler.get_summary(),
            "network": self.network_handler.get_summary()
        }
    
    def get_total_exceptions(self) -> int:
        """Get total number of exceptions across all handlers."""
        summaries = self.get_all_summaries()
        total = 0
        for handler_type, summary in summaries.items():
            for key, value in summary.items():
                if "total" in key and isinstance(value, int):
                    total += value
        return total

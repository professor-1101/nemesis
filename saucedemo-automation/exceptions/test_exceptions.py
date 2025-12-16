"""Test execution exception handling."""

from typing import Any, Dict, Optional


class TestExceptionHandler:
    """Handles test execution exceptions."""
    
    def __init__(self, logger=None):
        """Initialize test exception handler."""
        self.logger = logger
        self.exception_count = 0
    
    def handle_test_failure(self, exception: Exception, test_info: Dict[str, Any] = None):
        """Handle test failure exceptions."""
        self.exception_count += 1
        
        exception_info = {
            "type": "test_failure",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "test_info": test_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_assertion_error(self, exception: Exception, assertion_info: Dict[str, Any] = None):
        """Handle assertion errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "assertion_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "assertion_info": assertion_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_step_failure(self, exception: Exception, step_info: Dict[str, Any] = None):
        """Handle step failure exceptions."""
        self.exception_count += 1
        
        exception_info = {
            "type": "step_failure",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "step_info": step_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_scenario_failure(self, exception: Exception, scenario_info: Dict[str, Any] = None):
        """Handle scenario failure exceptions."""
        self.exception_count += 1
        
        exception_info = {
            "type": "scenario_failure",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "scenario_info": scenario_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def _log_exception(self, exception_info: Dict[str, Any], exception: Exception):
        """Log exception details."""
        if self.logger:
            self.logger.error(
                f"Test Exception [{exception_info['type']}]: {exception_info['message']}",
                exception=exception,
                **exception_info
            )
        else:
            # Fallback to structured logging
            import json
            log_entry = {
                "timestamp": __import__('time').time(),
                "level": "ERROR",
                "message": f"Test Exception [{exception_info['type']}]: {exception_info['message']}",
                "exception_info": exception_info,
                "exception_type": type(exception).__name__
            }
            print(json.dumps(log_entry, ensure_ascii=False))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get exception summary."""
        return {
            "total_test_exceptions": self.exception_count,
            "handler_status": "active"
        }

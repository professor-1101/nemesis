"""Environment-related exception handling."""

from typing import Any, Dict, Optional


class EnvironmentExceptionHandler:
    """Handles environment setup and configuration exceptions."""
    
    def __init__(self, logger=None):
        """Initialize environment exception handler."""
        self.logger = logger
        self.exception_count = 0
    
    def handle_setup_error(self, exception: Exception, context: Dict[str, Any] = None):
        """Handle environment setup errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "environment_setup_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "count": self.exception_count,
            "context": context or {}
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_config_error(self, exception: Exception, config_name: str = None):
        """Handle configuration errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "configuration_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "config_name": config_name,
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_initialization_error(self, exception: Exception, component: str = None):
        """Handle component initialization errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "initialization_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "component": component,
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def _log_exception(self, exception_info: Dict[str, Any], exception: Exception):
        """Log exception details."""
        if self.logger:
            self.logger.error(
                f"Environment Exception [{exception_info['type']}]: {exception_info['message']}",
                exception=exception,
                **exception_info
            )
        else:
            # Fallback to structured logging
            import json
            log_entry = {
                "timestamp": __import__('time').time(),
                "level": "ERROR",
                "message": f"Environment Exception [{exception_info['type']}]: {exception_info['message']}",
                "exception_info": exception_info,
                "exception_type": type(exception).__name__
            }
            print(json.dumps(log_entry, ensure_ascii=False))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get exception summary."""
        return {
            "total_environment_exceptions": self.exception_count,
            "handler_status": "active"
        }

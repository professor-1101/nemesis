"""Validation-related exception handling."""

from typing import Any, Dict, Optional


class ValidationExceptionHandler:
    """Handles validation and form-related exceptions."""
    
    def __init__(self, logger=None):
        """Initialize validation exception handler."""
        self.logger = logger
        self.exception_count = 0
    
    def handle_form_validation_error(self, exception: Exception, form_info: Dict[str, Any] = None):
        """Handle form validation errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "form_validation_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "form_info": form_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_input_validation_error(self, exception: Exception, input_info: Dict[str, Any] = None):
        """Handle input validation errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "input_validation_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "input_info": input_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_data_validation_error(self, exception: Exception, data_info: Dict[str, Any] = None):
        """Handle data validation errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "data_validation_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "data_info": data_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_credential_validation_error(self, exception: Exception, credential_info: Dict[str, Any] = None):
        """Handle credential validation errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "credential_validation_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "credential_info": credential_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def _log_exception(self, exception_info: Dict[str, Any], exception: Exception):
        """Log exception details."""
        if self.logger:
            self.logger.error(
                f"Validation Exception [{exception_info['type']}]: {exception_info['message']}",
                exception=exception,
                **exception_info
            )
        else:
            # Fallback to structured logging
            import json
            log_entry = {
                "timestamp": __import__('time').time(),
                "level": "ERROR",
                "message": f"Validation Exception [{exception_info['type']}]: {exception_info['message']}",
                "exception_info": exception_info,
                "exception_type": type(exception).__name__
            }
            print(json.dumps(log_entry, ensure_ascii=False))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get exception summary."""
        return {
            "total_validation_exceptions": self.exception_count,
            "handler_status": "active"
        }

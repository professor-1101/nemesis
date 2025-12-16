"""Network-related exception handling."""

from typing import Any, Dict, Optional


class NetworkExceptionHandler:
    """Handles network and connectivity exceptions."""
    
    def __init__(self, logger=None):
        """Initialize network exception handler."""
        self.logger = logger
        self.exception_count = 0
    
    def handle_connection_error(self, exception: Exception, connection_info: Dict[str, Any] = None):
        """Handle connection errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "connection_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "connection_info": connection_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_timeout_error(self, exception: Exception, timeout_info: Dict[str, Any] = None):
        """Handle network timeout errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "network_timeout_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "timeout_info": timeout_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_http_error(self, exception: Exception, http_info: Dict[str, Any] = None):
        """Handle HTTP errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "http_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "http_info": http_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_dns_error(self, exception: Exception, dns_info: Dict[str, Any] = None):
        """Handle DNS resolution errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "dns_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "dns_info": dns_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def _log_exception(self, exception_info: Dict[str, Any], exception: Exception):
        """Log exception details."""
        if self.logger:
            self.logger.error(
                f"Network Exception [{exception_info['type']}]: {exception_info['message']}",
                exception=exception,
                **exception_info
            )
        else:
            # Fallback to structured logging
            import json
            log_entry = {
                "timestamp": __import__('time').time(),
                "level": "ERROR",
                "message": f"Network Exception [{exception_info['type']}]: {exception_info['message']}",
                "exception_info": exception_info,
                "exception_type": type(exception).__name__
            }
            print(json.dumps(log_entry, ensure_ascii=False))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get exception summary."""
        return {
            "total_network_exceptions": self.exception_count,
            "handler_status": "active"
        }

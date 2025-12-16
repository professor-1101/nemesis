"""Browser-related exception handling."""

from typing import Any, Dict, Optional


class BrowserExceptionHandler:
    """Handles browser and webdriver exceptions."""
    
    def __init__(self, logger=None):
        """Initialize browser exception handler."""
        self.logger = logger
        self.exception_count = 0
    
    def handle_browser_start_error(self, exception: Exception, browser_type: str = None):
        """Handle browser startup errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "browser_start_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "browser_type": browser_type,
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_element_not_found(self, exception: Exception, element_info: Dict[str, Any] = None):
        """Handle element not found errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "element_not_found",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "element_info": element_info or {},
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_timeout_error(self, exception: Exception, timeout_duration: int = None):
        """Handle timeout errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "timeout_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "timeout_duration": timeout_duration,
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def handle_navigation_error(self, exception: Exception, url: str = None):
        """Handle navigation errors."""
        self.exception_count += 1
        
        exception_info = {
            "type": "navigation_error",
            "message": str(exception),
            "exception_class": exception.__class__.__name__,
            "url": url,
            "count": self.exception_count
        }
        
        self._log_exception(exception_info, exception)
        return exception_info
    
    def _log_exception(self, exception_info: Dict[str, Any], exception: Exception):
        """Log exception details."""
        if self.logger:
            self.logger.error(
                f"Browser Exception [{exception_info['type']}]: {exception_info['message']}",
                exception=exception,
                **exception_info
            )
        else:
            # Fallback to structured logging
            import json
            log_entry = {
                "timestamp": __import__('time').time(),
                "level": "ERROR",
                "message": f"Browser Exception [{exception_info['type']}]: {exception_info['message']}",
                "exception_info": exception_info,
                "exception_type": type(exception).__name__
            }
            print(json.dumps(log_entry, ensure_ascii=False))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get exception summary."""
        return {
            "total_browser_exceptions": self.exception_count,
            "handler_status": "active"
        }

"""Base collector class with common functionality for all collectors."""

import traceback
from typing import Any
from time import time


class BaseCollector:
    """Base class for collectors with common context manager and timestamp support."""

    @staticmethod
    def _get_timestamp() -> float:
        """Get current timestamp in milliseconds.
        
        Returns:
            Current timestamp in milliseconds
        """
        return time() * 1000

    def __enter__(self):
        """Context manager support.
        
        Returns:
            Self instance
        """
        return self

    def __exit__(self, exc_type: Any, _exc_val: Any, _exc_tb: Any) -> bool:
        """Cleanup on context exit.
        
        Args:
            exc_type: Exception type
            _exc_val: Exception value
            _exc_tb: Exception traceback
            
        Returns:
            False to allow exception propagation
        """
        try:
            self._cleanup_listeners()
        except (AttributeError, RuntimeError) as e:
            # Playwright page event listener errors - ignore during cleanup
            if hasattr(self, 'logger'):
                self.logger.debug(
                    f"Error during collector cleanup: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name=self.__class__.__name__,
                    method="__exit__"
                )
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
            raise
        return False

    def _cleanup_listeners(self) -> None:
        """Clean up listeners - must be implemented by subclasses.
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _cleanup_listeners")

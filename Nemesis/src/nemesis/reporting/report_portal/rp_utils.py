"""ReportPortal utility functions module.

This module provides utility functions for ReportPortal integration, including
timestamp generation, MIME type detection, attribute parsing, and stack trace
extraction.
"""
import traceback
from datetime import datetime
from pathlib import Path

class RPUtils:
    """Utility functions for ReportPortal integration.
    
    Provides helper methods for timestamp generation, MIME type detection,
    attribute parsing, and stack trace extraction.
    """
    @staticmethod
    def timestamp() -> str:
        """Get timestamp in milliseconds."""
        return str(int(datetime.now().timestamp() * 1000))

    @staticmethod
    def get_mime_type(file_path: Path) -> str:
        """Get MIME type from file extension."""
        ext = file_path.suffix.lower()
        mime_types = {
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.log': 'text/plain',
            '.webm': 'video/webm',
            '.mp4': 'video/mp4',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.zip': 'application/zip',
            '.har': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.pdf': 'application/pdf',
        }
        return mime_types.get(ext, 'application/octet-stream')

    @staticmethod
    def parse_attributes(attrs_str: str) -> list[dict[str, str]]:
        """Parse launch attributes from a string."""
        if not attrs_str:
            return []

        attributes = []
        for tag in attrs_str.split():
            tag = tag.strip()
            if tag:
                if ":" in tag:
                    key, value = tag.split(":", 1)
                    attributes.append({"key": key, "value": value})
                else:
                    attributes.append({"key": "tag", "value": tag})
        return attributes

    @staticmethod
    def extract_stack_trace(exception: Exception) -> str:
        """Extract stack trace from exception object."""
        try:
            if hasattr(exception, '__traceback__') and exception.__traceback__ is not None:
                return ''.join(traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__
                ))
            return ''.join(traceback.format_exception_only(type(exception), exception))
        except (AttributeError, TypeError, ValueError) as e:
            # Traceback extraction errors - attribute access or type issues
            # Fallback for when traceback extraction itself fails
            return f"{type(exception).__name__}: {str(exception)}\n(Stack trace extraction failed: {e})"
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from traceback extraction
            # NOTE: traceback.format_exception may raise various exceptions we cannot predict
            return f"{type(exception).__name__}: {str(exception)}\n(Stack trace extraction failed: {e})"

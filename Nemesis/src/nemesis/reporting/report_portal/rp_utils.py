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
        return RPUtils.get_mime_type_from_ext(ext)

    @staticmethod
    def get_mime_type_from_ext(ext: str) -> str:
        """Get MIME type from file extension string."""
        ext = ext.lower()
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

    @staticmethod
    def parse_behave_tags(tags: list) -> dict:
        """Parse Behave tags to extract attributes, test case IDs, and other metadata.

        Supports:
        - @attribute(key:value) -> Adds to attributes list
        - @test_case_id(TC-XXX) -> Sets test_case_id
        - @fixture.* -> Adds to attributes as fixture tag
        - Regular tags -> Adds to attributes as simple tags

        Args:
            tags: List of Behave tag strings

        Returns:
            Dictionary with parsed metadata:
            {
                'attributes': [{'key': 'tag', 'value': 'smoke'}, ...],
                'test_case_id': 'TC-001',
                'is_fixture': False
            }

        Examples:
            >>> RPUtils.parse_behave_tags(['smoke', 'attribute(priority:high)', 'test_case_id(TC-001)'])
            {
                'attributes': [
                    {'key': 'tag', 'value': 'smoke'},
                    {'key': 'priority', 'value': 'high'}
                ],
                'test_case_id': 'TC-001',
                'is_fixture': False
            }
        """
        result = {
            'attributes': [],
            'test_case_id': None,
            'is_fixture': False
        }

        if not tags:
            return result

        for tag in tags:
            tag_str = str(tag).strip()

            # Parse @attribute(key:value)
            if tag_str.startswith('attribute(') and tag_str.endswith(')'):
                attr_content = tag_str[10:-1]  # Remove "attribute(" and ")"
                if ':' in attr_content:
                    key, value = attr_content.split(':', 1)
                    result['attributes'].append({
                        'key': key.strip(),
                        'value': value.strip()
                    })
                else:
                    # If no colon, treat whole content as value with 'attribute' key
                    result['attributes'].append({
                        'key': 'attribute',
                        'value': attr_content.strip()
                    })

            # Parse @test_case_id(TC-XXX)
            elif tag_str.startswith('test_case_id(') and tag_str.endswith(')'):
                test_case_id = tag_str[13:-1]  # Remove "test_case_id(" and ")"
                result['test_case_id'] = test_case_id.strip()

            # Parse @fixture.* tags
            elif tag_str.startswith('fixture.') or tag_str == 'fixture':
                result['is_fixture'] = True
                result['attributes'].append({
                    'key': 'fixture',
                    'value': tag_str
                })

            # Regular tags - add as simple key-value pair
            else:
                result['attributes'].append({
                    'key': 'tag',
                    'value': tag_str
                })

        return result

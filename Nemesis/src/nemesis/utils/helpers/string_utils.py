"""String utility functions."""

import re
from typing import Any, Dict


class StringUtils:
    """String utility functions."""

    # Constants for validation
    MAX_FILENAME_LENGTH = 255
    VALID_FILENAME_CHARS = re.compile(r'[^a-zA-Z0-9._\-]')

    @staticmethod
    def sanitize_filename(name: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
        """Sanitize string for use as filename."""
        if not name:
            return "unnamed"

        # Replace invalid characters with underscore
        name = StringUtils.VALID_FILENAME_CHARS.sub('_', name)

        # Replace multiple underscores with single
        name = re.sub(r'_+', '_', name)

        # Remove leading/trailing underscores and dots
        name = name.strip('_.')

        # Ensure not empty after sanitization
        if not name:
            return "unnamed"

        # Truncate if too long (preserve extension if exists)
        if len(name) > max_length:
            if '.' in name:
                base, ext = name.rsplit('.', 1)
                max_base = max_length - len(ext) - 1
                name = base[:max_base] + '.' + ext
            else:
                name = name[:max_length]

        return name

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is valid URL."""
        if not url or not isinstance(url, str):
            return False

        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(url))

    @staticmethod
    def flatten_dict(
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '.'
    ) -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []

        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(StringUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

        return dict(items)

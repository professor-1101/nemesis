"""Sensitive Data Masker for Playwright adapters.

Responsibilities:
- Detect sensitive data patterns in selectors
- Mask sensitive values in logs
"""
from typing import List, Optional


class SensitiveDataMasker:
    """Handles sensitive data detection and masking for action logs."""

    # Default sensitive patterns for masking
    DEFAULT_SENSITIVE_PATTERNS = [
        "password", "passwd", "pwd",
        "token", "api_key", "apikey",
        "secret", "auth", "authorization"
    ]

    def __init__(
        self,
        sensitive_patterns: Optional[List[str]] = None,
        mask_character: str = "***"
    ) -> None:
        """
        Initialize sensitive data masker.

        Args:
            sensitive_patterns: List of patterns for sensitive data masking (case-insensitive)
            mask_character: Character/string to use for masking sensitive data
        """
        self._sensitive_patterns = sensitive_patterns or self.DEFAULT_SENSITIVE_PATTERNS
        self._mask_character = mask_character

    def is_sensitive_selector(self, selector: str) -> bool:
        """
        Check if selector contains sensitive data patterns.

        Args:
            selector: CSS/XPath selector

        Returns:
            True if selector matches any sensitive pattern
        """
        selector_lower = selector.lower()
        return any(
            pattern.lower() in selector_lower
            for pattern in self._sensitive_patterns
        )

    def mask_sensitive_value(self, value: str, selector: str = "") -> str:
        """
        Mask sensitive values based on selector patterns.

        Args:
            value: Value to potentially mask
            selector: Selector that may indicate sensitive data

        Returns:
            Original value or masked value if sensitive
        """
        if self.is_sensitive_selector(selector):
            return self._mask_character
        return value

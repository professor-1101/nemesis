"""Validation utility functions."""

import re


class ValidationUtils:
    """Validation utility functions."""

    @staticmethod
    def parse_size_string(size_str: str) -> int:
        """Parse human-readable size string to bytes."""
        size_str = size_str.strip().upper()

        # Extract number and unit
        match = re.match(r'^([\d.]+)\s*([KMGT]?B?)$', size_str)
        if not match:
            raise ValueError(f"Invalid size format: {size_str}")

        number, unit = match.groups()
        number = float(number)

        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4,
        }

        multiplier = units.get(unit, 1)
        return int(number * multiplier)

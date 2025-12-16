"""Configuration utilities for centralized config management."""

from typing import Optional
from pathlib import Path


class ConfigHelper:
    """Helper class for configuration management."""

    def __init__(self, config_loader=None):
        """Initialize config helper.

        Args:
            config_loader: ConfigLoader instance
        """
        self.config_loader = config_loader

    def get_path(self, key: str, default: Optional[str] = None) -> Path:
        """Get path from config and convert to Path object."""
        if self.config_loader:
            path_str = self.config_loader.get(key, default)
            if path_str:
                return Path(path_str)

        if default:
            return Path(default)

        raise ValueError(f"Path not found for key: {key}")

    def get_boolean(self, key: str, default: bool = False) -> bool:
        """Get boolean value from config."""
        if self.config_loader:
            return self.config_loader.get(key, default)
        return default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from config."""
        if self.config_loader:
            return self.config_loader.get(key, default)
        return default

    def get_string(self, key: str, default: str = "") -> str:
        """Get string value from config."""
        if self.config_loader:
            return self.config_loader.get(key, default)
        return default

    def get_list(self, key: str, default: Optional[list] = None) -> list:
        """Get list value from config."""
        if self.config_loader:
            return self.config_loader.get(key, default or [])
        return default or []

    def is_enabled(self, key: str, default: bool = False) -> bool:
        """Check if a feature is enabled."""
        return self.get_boolean(key, default)


# Global instance for backward compatibility
_config_helper: Optional[ConfigHelper] = None


def get_config_helper(config_loader=None) -> ConfigHelper:
    """Get global config helper instance."""
    global _config_helper
    if _config_helper is None:
        _config_helper = ConfigHelper(config_loader)
    return _config_helper


def set_config_helper(config_helper: ConfigHelper) -> None:
    """Set global config helper instance."""
    global _config_helper
    _config_helper = config_helper

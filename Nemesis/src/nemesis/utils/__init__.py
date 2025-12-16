"""Helper utilities - refactored into modular components."""
from pathlib import Path

# Import modular components
# Note: Pylint may show E0611 because helpers is both a module and a package
# Python correctly resolves to the package (helpers/) which has these modules
from .helpers.file_utils import FileUtils  # pylint: disable=no-name-in-module
from .helpers.string_utils import StringUtils  # pylint: disable=no-name-in-module
from .helpers.time_utils import TimeUtils  # pylint: disable=no-name-in-module
from .helpers.validation_utils import ValidationUtils  # pylint: disable=no-name-in-module
from .helpers.retry_utils import RetryUtils  # pylint: disable=no-name-in-module
from .path_utils import PathManager, get_path_manager, set_path_manager
from .config_utils import ConfigHelper, get_config_helper, set_config_helper

# Convenience functions for backward compatibility
def sanitize_filename(name: str, max_length: int = 255) -> str:
    """Sanitize filename - backward compatibility."""
    return StringUtils.sanitize_filename(name, max_length)

def generate_timestamp(format_str: str = "%Y-%m-%d_%H-%M-%S") -> str:
    """Generate timestamp - backward compatibility."""
    return TimeUtils.generate_timestamp(format_str)

def ensure_directory(path):
    """Ensure directory - backward compatibility."""
    return FileUtils.ensure_directory(Path(path))

def read_json_file(file_path):
    """Read JSON file - backward compatibility."""
    return FileUtils.read_json_file(Path(file_path))

def write_json_file(file_path, data, indent=2, backup=False):
    """Write JSON file - backward compatibility."""
    return FileUtils.write_json_file(Path(file_path), data, indent, backup)

def format_duration(seconds: float, precision: int = 2) -> str:
    """Format duration - backward compatibility."""
    return TimeUtils.format_duration(seconds, precision)

def calculate_file_hash(file_path, algorithm: str = "sha256") -> str:
    """Calculate file hash - backward compatibility."""
    return FileUtils.calculate_file_hash(Path(file_path), algorithm)

def parse_size_string(size_str: str) -> int:
    """Parse size string - backward compatibility."""
    return ValidationUtils.parse_size_string(size_str)

def is_valid_url(url: str) -> bool:
    """Check valid URL - backward compatibility."""
    return StringUtils.is_valid_url(url)

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten dict - backward compatibility."""
    return StringUtils.flatten_dict(d, parent_key, sep)

def retry_on_exception(func, max_attempts=3, delay=1.0, exceptions=(Exception,)):
    """Retry on exception - backward compatibility."""
    return RetryUtils.retry_on_exception(func, max_attempts, delay, exceptions)

__all__ = [
    # Classes
    "FileUtils", "StringUtils", "TimeUtils", "ValidationUtils", "RetryUtils",
    "PathManager", "ConfigHelper",
    # Functions
    "sanitize_filename", "generate_timestamp", "ensure_directory",
    "read_json_file", "write_json_file", "format_duration",
    "calculate_file_hash", "parse_size_string", "is_valid_url",
    "flatten_dict", "retry_on_exception",
    "get_path_manager", "set_path_manager",
    "get_config_helper", "set_config_helper"
]

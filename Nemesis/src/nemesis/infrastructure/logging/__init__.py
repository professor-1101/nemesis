"""Nemesis logging system - clean, modular architecture."""

from .factory import create_test_logger, create_framework_logger, get_factory
from .config.settings import LoggingConfig
from .context.manager import ContextManager
from .models.log_entry import LogEntry
from .legacy_wrapper import Logger

__all__ = [
    "create_test_logger",
    "create_framework_logger",
    "get_factory",
    "LoggingConfig",
    "ContextManager",
    "LogEntry",
    "Logger"  # For backward compatibility
]

# Example usage:
#
# # Test execution logging
# test_logger = create_test_logger()
# test_logger.info("Test step executed", step="login", browser="chromium")
#
# # Framework logging
# framework_logger = create_framework_logger()
# framework_logger.debug("Module initialized", module="logging")
#
# # Context management
# context_manager = get_factory().get_context_manager()
# context_manager.start_correlation(test_id="test_001")
# context_manager.end_correlation(status="completed")

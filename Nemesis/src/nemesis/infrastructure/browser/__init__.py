"""Browser management package - REFACTORED."""

from .browser_manager import BrowserManager
from .browser_lifecycle import BrowserLifecycle
from .browser_launcher import BrowserLauncher
from .browser_cleanup import BrowserCleanup
from .browser_health import BrowserHealthMonitor
from .browser_operations import BrowserOperations

__all__ = [
    'BrowserManager',
    'BrowserLifecycle',
    'BrowserLauncher',
    'BrowserCleanup',
    'BrowserHealthMonitor',
    'BrowserOperations'
]

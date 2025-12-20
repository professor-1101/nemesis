"""Data collectors package."""
from .console import ConsoleCollector
from .network import NetworkCollector
from .performance.performance_collector import PerformanceCollector

__all__ = [
    "ConsoleCollector",
    "NetworkCollector",
    "PerformanceCollector",
]


def get_collector(collector_type: str):
    """Get collector instance by type."""
    # This is a placeholder - in real implementation,
    # collectors should be managed by a collector coordinator
    # and accessible through environment manager
    from nemesis.infrastructure.environment.hooks import _get_env_manager
    env_manager = _get_env_manager()
    if env_manager and hasattr(env_manager, 'get_collector'):
        return env_manager.get_collector(collector_type)
    return None
"""Helper functions for browser configuration."""

from typing import Any


def _ensure_logger_on_config(config: Any, logger: Any) -> None:
    """Ensure logger is attached to config for helper functions.
    
    Args:
        config: Configuration loader instance
        logger: Logger instance to attach
    """
    if not hasattr(config, 'logger'):
        config.logger = logger


def get_browser_type(config: Any, logger: Any = None) -> str:
    """Get browser type from config with validation.
    
    Args:
        config: Configuration loader instance
        logger: Optional logger instance (will use config.logger if available)
        
    Returns:
        Validated browser type string ("chromium", "firefox", or "webkit")
    """
    if logger:
        _ensure_logger_on_config(config, logger)

    browser_type = config.get("playwright.browser.type", "chromium")
    valid_types = ["chromium", "firefox", "webkit"]

    if browser_type not in valid_types:
        config_logger = getattr(config, 'logger', None)
        if config_logger:
            config_logger.warning(
                f"Invalid browser type '{browser_type}', defaulting to chromium"
            )
        return "chromium"

    return browser_type


def get_browser_args(config: Any) -> list[str]:
    """Get browser launch arguments from config.
    
    Args:
        config: Configuration loader instance
        
    Returns:
        List of browser arguments
    """
    return config.get("playwright.browser.args", [])


def get_viewport(config: Any, logger: Any = None) -> dict[str, int]:
    """Get viewport configuration with validation.
    
    Args:
        config: Configuration loader instance
        logger: Optional logger instance (will use config.logger if available)
        
    Returns:
        Dictionary with 'width' and 'height' keys
    """
    if logger:
        _ensure_logger_on_config(config, logger)

    width = config.get("playwright.viewport.width", 1920)
    height = config.get("playwright.viewport.height", 1080)

    config_logger = getattr(config, 'logger', None)

    # Validate viewport dimensions
    if width < 320 or width > 7680:
        if config_logger:
            config_logger.warning(f"Invalid viewport width {width}, using 1920")
        width = 1920

    if height < 240 or height > 4320:
        if config_logger:
            config_logger.warning(f"Invalid viewport height {height}, using 1080")
        height = 1080

    return {"width": width, "height": height}

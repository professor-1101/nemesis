"""Default configuration values."""
import os
from pathlib import Path


def get_default_config():
    """Get default configuration."""
    return {
        "env": os.getenv("TEST_ENV", "dev"),
        "debug": os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
        "project_root": Path.cwd(),
        "reports_dir": os.getenv("NEMESIS_REPORTS_DIR", str(Path.cwd() / "reports")),
        "features_dir": os.getenv("NEMESIS_FEATURES_DIR", str(Path.cwd() / "features")),
        "playwright": {
            "browser": {
                "type": "chromium",
                "headless": os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes"),
                "slow_mo": 0,
            },
            "viewport": {
                "width": 1920,
                "height": 1080,
            },
            "timeouts": {
                "default": 30000,
                "navigation": 30000,
                "action": 10000,
            },
        },
        "reporting": {
            "mode": "all",
            "local": {
                "enabled": True,
                "format": "html",
                "auto_open": False,
            },
        },
        "attachments": {
            "screenshots": {
                "enabled": True,
                "format": "png",
                "quality": 90,
            },
            "videos": {
                "enabled": False,  # Resource-intensive, disabled by default
                "format": "webm",
                "quality": "medium",
            },
            "traces": {
                "enabled": True,
                "format": "zip",
                "include_sources": True,
            },
            "network": {
                "enabled": True,
                "format": "har",
                "include_responses": False,
            },
            "performance": {
                "enabled": True,
                "format": "json",
                "metrics": ["timing", "memory", "network"],
            },
            "console": {
                "enabled": True,
                "format": "jsonl",
                "levels": ["error", "warning", "info"],
            },
        },
        "logging": {
            "level": "INFO",
            "format": "structured",
        },
    }

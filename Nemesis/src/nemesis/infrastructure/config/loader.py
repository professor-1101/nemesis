"""Configuration loader for Nemesis."""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from configparser import ConfigParser
from rich.console import Console

from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback

from .defaults import get_default_config
from .validator import ConfigValidator

LOGGER = Logger.get_instance({})

console = Console()


class ConfigLoader:
    """Load and merge configuration from multiple sources."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config loader.

        Args:
            config_dir: Path to config directory (default: ./conf or ./config)
        """
        self.config_dir = self._find_config_dir(config_dir)
        self.validator = ConfigValidator()
        self._config_cache: Optional[Dict[str, Any]] = None

    def _find_config_dir(self, config_dir: Optional[Path]) -> Path:
        """Find configuration directory."""
        if config_dir and config_dir.exists():
            return config_dir

        # Try common locations
        for dirname in ["conf", "config", "configs"]:
            path = Path.cwd() / dirname
            if path.exists():
                return path

        # Default to conf
        return Path.cwd() / "conf"

    def load(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load complete configuration.

        Args:
            force_reload: Force reload even if cached

        Returns:
            Complete merged configuration
        """
        if self._config_cache and not force_reload:
            return self._config_cache

        # Start with defaults
        config = get_default_config()

        # Load each config file
        config["playwright"] = self._load_playwright_config()
        config["reportportal"] = self._load_reportportal_config()
        config["behave"] = self._load_behave_config()
        config["logging"] = self._load_logging_config()
        config["reporting"] = self._load_reporting_config()

        # Extract attachments from playwright config (centralized)
        if "attachments" in config["playwright"]:
            config["attachments"] = config["playwright"]["attachments"]

        # Merge reportportal config into reporting config for backward compatibility
        if config["reportportal"] and config["reporting"].get("reportportal", {}).get("enabled", False):
            config["reporting"]["reportportal"].update(config["reportportal"])

        # Apply environment overrides
        config = self._apply_env_overrides(config)

        # Validate
        validation_result = self.validator.validate(config)
        if not validation_result["valid"]:
            console.print("[yellow]⚠ Configuration warnings:[/yellow]")
            for error in validation_result["errors"]:
                console.print(f"  [dim]• {error}[/dim]")

        self._config_cache = config
        return config

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, FileNotFoundError, yaml.YAMLError, UnicodeDecodeError),
        specific_message="Failed to load playwright.yaml: {error}",
        fallback_message="Failed to load playwright.yaml: {error}",
        return_on_error={}
    )
    def _load_playwright_config(self) -> Dict[str, Any]:
        """Load Playwright configuration."""
        config_file = self.config_dir / "playwright.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, FileNotFoundError, yaml.YAMLError, UnicodeDecodeError),
        specific_message="Failed to load reportportal.yaml: {error}",
        fallback_message="Failed to load reportportal.yaml: {error}",
        return_on_error={}
    )
    def _load_reportportal_config(self) -> Dict[str, Any]:
        """Load ReportPortal configuration."""
        config_file = self.config_dir / "reportportal.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            # Apply environment variable substitution
            config = self._substitute_env_vars(config)
            return config

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, FileNotFoundError, ValueError, TypeError),
        specific_message="Failed to load behave.ini: {error}",
        fallback_message="Failed to load behave.ini: {error}",
        return_on_error={}
    )
    def _load_behave_config(self) -> Dict[str, Any]:
        """Load Behave configuration from behave.ini."""
        config_file = self.config_dir / "behave.ini"
        if not config_file.exists():
            return {}

        parser = ConfigParser()
        parser.read(config_file)

        config = {}
        if parser.has_section("behave"):
            config["behave"] = dict(parser.items("behave"))
        if parser.has_section("behave.userdata"):
            config["userdata"] = dict(parser.items("behave.userdata"))
        if parser.has_section("report_portal"):
            config["report_portal"] = dict(parser.items("report_portal"))

        return config

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, FileNotFoundError, yaml.YAMLError, UnicodeDecodeError),
        specific_message="Failed to load logging.yaml: {error}",
        fallback_message="Failed to load logging.yaml: {error}",
        return_on_error={}
    )
    def _load_logging_config(self) -> Dict[str, Any]:
        """Load logging configuration."""
        config_file = self.config_dir / "logging.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            config = self._substitute_env_vars(config)
            return config

    @handle_exceptions_with_fallback(
        log_level="warning",
        specific_exceptions=(OSError, IOError, FileNotFoundError, yaml.YAMLError, UnicodeDecodeError),
        specific_message="Failed to load reporting.yaml: {error}",
        fallback_message="Failed to load reporting.yaml: {error}",
        return_on_error={}
    )
    def _load_reporting_config(self) -> Dict[str, Any]:
        """Load reporting configuration."""
        config_file = self.config_dir / "reporting.yaml"
        if not config_file.exists():
            return {}

        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config."""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        if isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        if isinstance(config, str):
            # Handle ${VAR:-default} syntax
            if config.startswith("${") and config.endswith("}"):
                var_expr = config[2:-1]
                if ":-" in var_expr:
                    var_name, default = var_expr.split(":-", 1)
                    return os.getenv(var_name, default)
                return os.getenv(var_expr, config)
            return config
        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        # TEST_ENV
        if "TEST_ENV" in os.environ:
            config["env"] = os.environ["TEST_ENV"]

        # HEADLESS
        if "HEADLESS" in os.environ:
            headless = os.environ["HEADLESS"].lower() in ("true", "1", "yes")
            if "playwright" not in config:
                config["playwright"] = {}
            if "browser" not in config["playwright"]:
                config["playwright"]["browser"] = {}
            config["playwright"]["browser"]["headless"] = headless

        # DEBUG
        if "DEBUG" in os.environ:
            debug = os.environ["DEBUG"].lower() in ("true", "1", "yes")
            config["debug"] = debug

        # RP_ENABLED
        if "RP_ENABLED" in os.environ:
            rp_enabled = os.environ["RP_ENABLED"].lower() in ("true", "1", "yes")
            if "reportportal" not in config:
                config["reportportal"] = {}
            config["reportportal"]["enabled"] = rp_enabled

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., "playwright.browser.type")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self.load()

        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def config_exists(self) -> bool:
        """Check if configuration directory and files exist."""
        if not self.config_dir.exists():
            return False

        required_files = ["playwright.yaml", "reporting.yaml"]
        for filename in required_files:
            if not (self.config_dir / filename).exists():
                return False

        return True

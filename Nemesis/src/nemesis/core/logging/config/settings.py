"""Configuration settings for logging system."""

from dataclasses import dataclass
from typing import List


@dataclass
class LocalConfig:
    """Local channel configuration."""
    output_dir: str = "${NEMESIS_REPORTS_DIR:-reports}/{execution_id}/logs/"
    filename_template: str = "logs.jsonl"
    file_rotation_size: int = 10485760  # 10MB
    max_files: int = 5


@dataclass
class LoggingConfig:
    """Main logging configuration."""

    # Service settings
    service_name: str = "nemesis"
    module: str = "core"
    operation_type: str = "logging"
    log_level: str = "INFO"

    # Channel settings
    enabled_channels: List[str] = None
    local_config: LocalConfig = None

    # Batch processing
    batch_enabled: bool = False
    batch_size: int = 100
    batch_timeout: float = 5.0
    max_queue_size: int = 1000

    # Retry settings
    retry_attempts: int = 3
    retry_backoff: float = 1.0

    def __post_init__(self):
        if self.enabled_channels is None:
            self.enabled_channels = ["local"]
        if self.local_config is None:
            self.local_config = LocalConfig()

    @classmethod
    def for_test_execution(cls) -> "LoggingConfig":
        """Create configuration for test execution."""
        try:
            from nemesis.core.config import ConfigLoader
            from nemesis.utils import get_config_helper

            config = ConfigLoader()
            config_helper = get_config_helper(config)

            log_level = config_helper.get_string("logging.level", "INFO")
            channels = config_helper.get_list("logging.enabled_channels", ["local"])

            # Get local config from centralized config
            local_config = LocalConfig(
                output_dir=config_helper.get_string("logging.output_dir",
                                                   "${NEMESIS_REPORTS_DIR:-reports}/{execution_id}/logs/"),
                file_rotation_size=config_helper.get_int("logging.file_rotation_size", 10485760),
                max_files=config_helper.get_int("logging.max_files", 5)
            )

            return cls(
                service_name="test-execution",
                module="test_execution",
                operation_type="test_execution",
                log_level=log_level,
                enabled_channels=channels,
                local_config=local_config
            )
        except Exception:
            # Fallback to defaults
            return cls()

    @classmethod
    def for_framework(cls) -> "LoggingConfig":
        """Create configuration for framework."""
        try:
            from nemesis.core.config import ConfigLoader
            from nemesis.utils import get_config_helper

            config = ConfigLoader()
            config_helper = get_config_helper(config)

            log_level = config_helper.get_string("logging.level", "DEBUG")
            channels = config_helper.get_list("logging.enabled_channels", ["local"])

            # Get local config from centralized config
            local_config = LocalConfig(
                output_dir=config_helper.get_string("logging.output_dir",
                                                   "${NEMESIS_REPORTS_DIR:-reports}/{execution_id}/logs/"),
                file_rotation_size=config_helper.get_int("logging.file_rotation_size", 10485760),
                max_files=config_helper.get_int("logging.max_files", 5)
            )

            return cls(
                service_name="nemesis-framework",
                module="framework",
                operation_type="framework_operation",
                log_level=log_level,
                enabled_channels=channels,
                local_config=local_config
            )
        except Exception:
            # Fallback to defaults
            return cls()

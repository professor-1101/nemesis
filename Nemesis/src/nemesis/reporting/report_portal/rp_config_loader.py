"""ReportPortal configuration loader module.

This module loads and validates ReportPortal configuration from configuration
file and environment variables, providing structured access to settings.
"""
import os
from typing import Any, Dict

from nemesis.infrastructure.config import ConfigLoader
from nemesis.shared.exceptions import ReportPortalError
from nemesis.infrastructure.logging import Logger
from .rp_utils import RPUtils

class RPConfigLoader:
    """Loads and validates ReportPortal configuration.
    
    Retrieves ReportPortal settings from configuration file and environment
    variables, validates required fields, and provides structured access
    to settings.
    """
    def __init__(self, config_loader: ConfigLoader) -> None:
        """Initialize ReportPortal config loader.
        
        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader
        self.logger = Logger.get_instance({})
        self._load_config()

    def _load_config(self) -> None:
        self.endpoint = self.config_loader.get("reportportal.endpoint") or os.getenv("RP_ENDPOINT")
        self.project = self.config_loader.get("reportportal.project") or os.getenv("RP_PROJECT")
        self.api_key = self.config_loader.get("reportportal.api_key") or os.getenv("RP_API_KEY")
        self.verify_ssl = self.config_loader.get("reportportal.verify_ssl", True)
        self.launch_name = self.config_loader.get("reportportal.launch_name", "Nemesis Automation")
        self.launch_description = self.config_loader.get("reportportal.launch_description")
        self.launch_attributes = RPUtils.parse_attributes(self.config_loader.get("reportportal.launch_attributes", ""))

        # Step log layout: SCENARIO (logs only), STEP (flat items), NESTED (hierarchical)
        step_log_layout = self.config_loader.get("reporting.reportportal.step_log_layout", "NESTED")
        self.step_log_layout = self._validate_step_layout(step_log_layout)

        # Skip handling: Whether skipped tests should be marked as issues
        self.is_skipped_an_issue = self.config_loader.get("reporting.reportportal.is_skipped_an_issue", False)

        # Debug mode: Creates DEBUG launches for testing/development
        self.debug_mode = self.config_loader.get("reporting.reportportal.debug_mode", False)

        self._validate_config()

    def _validate_step_layout(self, layout: str) -> str:
        """Validate step log layout configuration.

        Args:
            layout: Layout mode string

        Returns:
            Validated layout mode (uppercase)
        """
        valid_layouts = {"SCENARIO", "STEP", "NESTED"}
        layout_upper = layout.upper() if layout else "NESTED"

        if layout_upper not in valid_layouts:
            self.logger.warning(
                f"Invalid step_log_layout '{layout}'. Using default 'NESTED'. "
                f"Valid options: {', '.join(valid_layouts)}"
            )
            return "NESTED"

        return layout_upper

    def _validate_config(self) -> None:
        missing = []
        if not self.endpoint:
            missing.append("endpoint")
        if not self.project:
            missing.append("project")
        if not self.api_key:
            missing.append("api_key")

        if missing:
            raise ReportPortalError(
                "Missing ReportPortal configuration",
                f"Required fields: {', '.join(missing)}"
            )
        self.logger.info(
            f"ReportPortal configured: {self.endpoint} / {self.project}"
        )

    def get_rp_settings(self) -> Dict[str, Any]:
        """Get all ReportPortal settings as a dictionary.

        Returns:
            Dictionary containing all ReportPortal configuration settings:
            - endpoint: Server endpoint URL
            - project: Project name
            - api_key: API key for authentication
            - verify_ssl: SSL verification flag
            - launch_name: Launch name
            - launch_description: Launch description
            - launch_attributes: Launch attributes list
            - step_log_layout: Step logging layout mode
            - is_skipped_an_issue: Whether skipped tests are marked as issues
            - debug_mode: Whether to create DEBUG launches
        """
        return {
            "endpoint": self.endpoint,
            "project": self.project,
            "api_key": self.api_key,
            "verify_ssl": self.verify_ssl,
            "launch_name": self.launch_name,
            "launch_description": self.launch_description,
            "launch_attributes": self.launch_attributes,
            "step_log_layout": self.step_log_layout,
            "is_skipped_an_issue": self.is_skipped_an_issue,
            "debug_mode": self.debug_mode,
        }

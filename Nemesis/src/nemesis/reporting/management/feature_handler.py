"""Feature management for reporting."""
from typing import Any, List, Dict
from nemesis.infrastructure.logging import Logger
from nemesis.utils.decorators.exception_handler import handle_exceptions_with_fallback


class FeatureHandler:
    """Handles feature reporting."""

    def __init__(self, reporter_manager):
        """Initialize feature handler."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

    @handle_exceptions_with_fallback(
        log_level="debug",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="Failed to log to local reporter: {error}",
        fallback_message="Failed to log to local reporter: {error}"
    )
    def _log_to_local_reporter(self, message: str) -> None:
        """Log message to local reporter with exception handling."""
        self.reporter_manager.get_local_reporter().add_log(message, "INFO")

    @handle_exceptions_with_fallback(
        log_level="error",
        specific_exceptions=(AttributeError, RuntimeError),
        specific_message="{error}",
        fallback_message="{error}"
    )
    def _extract_launch_attributes(self, feature) -> List[Dict[str, Any]]:
        """Extract launch attributes from feature and configuration.

        Required attributes per RP requirements:
        - browser_type: Browser type
        - scenario_count: Number of scenarios in feature
        - version: Software version
        - sprint: Sprint name
        - environment: One of [product, infra, QA]

        Returns:
            List of attribute dictionaries with 'key' and 'value' fields
        """
        attributes = []

        # Get scenario count from feature
        scenarios = getattr(feature, 'scenarios', [])
        scenario_count = len(scenarios)
        attributes.append({"key": "scenario_count", "value": str(scenario_count)})

        # Get other attributes from config or environment
        config = self.reporter_manager.config

        # Browser type (try to get from config, fallback to environment)
        browser_type = config.get("browser.type", "Chrome")  # Default fallback
        attributes.append({"key": "browser_type", "value": browser_type})

        # Version (from config or environment)
        version = config.get("app.version", "1.0.0")
        attributes.append({"key": "version", "value": version})

        # Sprint (from config or environment)
        sprint = config.get("app.sprint", "Unknown")
        attributes.append({"key": "sprint", "value": sprint})

        # Environment (must be one of: product, infra, QA)
        env = config.get("app.environment", "QA")
        if env not in ["product", "infra", "QA"]:
            env = "QA"  # Default fallback
        attributes.append({"key": "environment", "value": env})

        self.logger.info(f"[RP DEBUG] Extracted launch attributes: {attributes}")
        return attributes

    def _call_rp_client(self, callback) -> None:
        """Call ReportPortal client method with exception handling."""
        try:
            callback()
        except Exception as e:
            # Log the error for debugging
            self.logger.error(f"Error calling RP client: {e}", exc_info=True)
            raise

    def start_feature(self, feature) -> None:
        """Start feature reporting with support for advanced tags."""
        feature_name = getattr(feature, 'name', str(feature))
        description = getattr(feature, 'description', '')
        tags = getattr(feature, 'tags', [])

        self.logger.feature_start(feature_name)

        # Update environment context for attachment naming
        from nemesis.infrastructure.environment.hooks import _get_env_manager
        env_manager = _get_env_manager()
        if env_manager:
            env_manager.set_current_feature(feature_name)

        if self.reporter_manager.is_local_enabled():
            self._log_to_local_reporter(f"Feature started: {feature_name}")

        if self.reporter_manager.is_rp_enabled():
            rp_client = self.reporter_manager.get_rp_client()
            if not rp_client:
                self.logger.warning("ReportPortal client is None, cannot start feature")
                return

            # Extract launch attributes from feature and config
            launch_attributes = self._extract_launch_attributes(feature)

            desc_text = '\n'.join(description) if isinstance(description, list) else description
            self.logger.info(f"[RP DEBUG] Calling start_feature: feature_name={feature_name}, description length={len(desc_text)}, tags={tags}")
            self._call_rp_client(
                lambda: rp_client.start_feature(feature_name, desc_text, tags, launch_attributes=launch_attributes)
            )
            self.logger.info(f"[RP DEBUG] After start_feature: launch_id={rp_client.launch_id if rp_client else 'N/A'}")

    def end_feature(self, feature, status: str = None) -> None:
        """End feature reporting.

        Args:
            feature: Feature object
            status: Status string ("passed" or "failed") - if None, will be extracted from feature
        """
        feature_name = getattr(feature, 'name', str(feature))

        # Use provided status or extract from feature
        if status is None:
            feature_status = getattr(feature, 'status', None)
            if hasattr(feature_status, 'name'):
                status = feature_status.name  # "passed" or "failed"
            elif isinstance(feature_status, str):
                status = feature_status.lower()
            else:
                # Try to determine from scenarios
                status = "passed"  # Default to passed

        # Normalize to uppercase for ReportPortal
        status_str = "PASSED" if status.lower() in ("passed", "pass") else "FAILED"

        self.logger.feature_end(feature_name, status_str)

        if self.reporter_manager.is_local_enabled():
            self._log_to_local_reporter(f"Feature ended: {feature_name} - Status: {status_str}")

        if self.reporter_manager.is_rp_enabled():
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().finish_feature(status_str),
                "Failed to finish feature in ReportPortal"
            )

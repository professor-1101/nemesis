"""Feature management for reporting."""
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
    def _call_rp_client(self, callback) -> None:
        """Call ReportPortal client method with exception handling."""
        callback()

    def start_feature(self, feature) -> None:
        """Start feature reporting with support for advanced tags."""
        feature_name = getattr(feature, 'name', str(feature))
        description = getattr(feature, 'description', '')
        tags = getattr(feature, 'tags', [])

        self.logger.feature_start(feature_name)

        if self.reporter_manager.is_local_enabled():
            self._log_to_local_reporter(f"Feature started: {feature_name}")

        if self.reporter_manager.is_rp_enabled():
            desc_text = '\n'.join(description) if isinstance(description, list) else description
            self._call_rp_client(
                lambda: self.reporter_manager.get_rp_client().start_feature(feature_name, desc_text, tags),
                "Failed to start feature in ReportPortal"
            )

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

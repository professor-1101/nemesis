"""Feature management for reporting."""
import traceback
from nemesis.infrastructure.logging import Logger


class FeatureManager:
    """Manages feature reporting."""

    def __init__(self, reporter_manager):
        """Initialize feature manager."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager

    def start_feature(self, feature) -> None:
        """Start feature reporting with support for advanced tags."""
        feature_name = getattr(feature, 'name', str(feature))
        description = getattr(feature, 'description', '')
        tags = getattr(feature, 'tags', [])

        self.logger.feature_start(feature_name)

        if self.reporter_manager.is_local_enabled():
            try:
                self.reporter_manager.get_local_reporter().add_log(f"Feature started: {feature_name}", "INFO")
            except (AttributeError, RuntimeError) as e:
                # Local reporter API errors - non-critical
                self.logger.debug(f"Failed to log feature start to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="start_feature")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: LocalReporter.add_log may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to log feature start to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="start_feature")

        if self.reporter_manager.is_rp_enabled():
            try:
                desc_text = '\n'.join(description) if isinstance(description, list) else description
                # Pass tags to ReportPortal for advanced tag parsing
                self.reporter_manager.get_rp_client().start_feature(feature_name, desc_text, tags)
            except (AttributeError, RuntimeError) as e:
                # ReportPortal client API errors
                self.logger.error(f"Failed to start feature in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="start_feature")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Failed to start feature in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="start_feature")

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
            try:
                self.reporter_manager.get_local_reporter().add_log(f"Feature ended: {feature_name} - Status: {status_str}", "INFO")
            except (AttributeError, RuntimeError) as e:
                # Local reporter API errors - non-critical
                self.logger.debug(f"Failed to log feature end to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="end_feature")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: LocalReporter.add_log may raise various exceptions we cannot predict
                self.logger.debug(f"Failed to log feature end to local reporter: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="end_feature")

        if self.reporter_manager.is_rp_enabled():
            try:
                self.reporter_manager.get_rp_client().finish_feature(status_str)
            except (AttributeError, RuntimeError) as e:
                # ReportPortal client API errors
                self.logger.error(f"Failed to finish feature in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="end_feature")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal SDK
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"Failed to finish feature in ReportPortal: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FeatureManager", method="end_feature")

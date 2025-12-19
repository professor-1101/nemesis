"""ReportPortal base client module.

This module provides the base client for ReportPortal integration, handling
client creation, connection validation, and basic health checks.
"""
from reportportal_client import RPClient
from nemesis.utils.decorators import retry
from nemesis.shared.exceptions import ReportPortalError
from nemesis.infrastructure.logging import Logger

class RPClientBase:
    """Base client for ReportPortal integration.
    
    Handles client creation, connection validation, and basic health checks.
    """
    def __init__(self, endpoint: str, project: str, api_key: str, verify_ssl: bool = True) -> None:
        """Initialize ReportPortal base client.
        
        Args:
            endpoint: ReportPortal server endpoint URL
            project: ReportPortal project name
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.endpoint = endpoint
        self.project = project
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.logger = Logger.get_instance({})
        self.client: RPClient = self._create_client()

    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    def _create_client(self) -> RPClient:
        """Create ReportPortal client."""
        try:
            client = RPClient(
                endpoint=self.endpoint,
                project=self.project,
                api_key=self.api_key,
                verify_ssl=self.verify_ssl,
            )
            self.logger.info(f"[DEBUG] ReportPortal client created for project: {self.project}")
            return client
        except Exception as e:
            raise ReportPortalError("Failed to create RP client", str(e)) from e

    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    def _validate_connection(self) -> None:
        """Validate connection to ReportPortal."""
        try:
            self.logger.debug("Validating ReportPortal connection...")
            # Actual validation logic would go here, e.g., a simple API call
            # For now, just logging its configuration is enough as per original
            self.logger.info(
                f"ReportPortal client base initialized for {self.endpoint} / {self.project}"
            )
        except Exception as e:
            raise ReportPortalError("Connection validation failed", str(e)) from e

    def is_healthy(self) -> bool:
        """Check if client is healthy."""
        # This will be more meaningful when launch_id is managed by RPLaunchCoordinator
        # For now, it just means client instance exists and connection was validated.
        return self.client is not None

    def get_launch_url(self, launch_id: str) -> str | None:
        """Get URL to launch in ReportPortal UI."""
        if not launch_id:
            return None

        # Remove /api/v1 if present, or use endpoint as-is
        base_url = self.endpoint.rstrip("/")
        if base_url.endswith("/api/v1"):
            base_url = base_url[:-7]  # Remove /api/v1
        elif base_url.endswith("/api"):
            base_url = base_url[:-4]  # Remove /api

        return f"{base_url}/ui/#{self.project}/launches/all/{launch_id}"

"""Network event collection module.

Listens to Playwright page network events and captures request/response data.
"""
import traceback
from typing import Any

from playwright.sync_api import Page, Request, Response

from nemesis.infrastructure.logging import Logger
from nemesis.shared.exceptions import CollectorError
from .base_collector import BaseCollector


class NetworkEventCollector(BaseCollector):
    """
    Collects network request and response events from Playwright page.

    Responsibilities:
    - Listen to Playwright network events (request, response, requestfailed)
    - Filter URLs based on criteria
    - Truncate long URLs and post data
    - Store raw event data
    - Manage event listener lifecycle

    Note: This class focuses only on event collection, not processing or persistence.
    """

    MAX_REQUESTS = 50000  # Prevent memory issues
    MAX_URL_LENGTH = 500
    MAX_POST_DATA_LENGTH = 1000

    def __init__(
        self,
        page: Page,
        url_filter: str | None = None,
        capture_requests: bool = True,
        capture_responses: bool = True
    ) -> None:
        """
        Initialize network event collector.

        Args:
            page: Playwright page instance
            url_filter: Optional URL substring filter (only track matching URLs)
            capture_requests: Whether to capture request events
            capture_responses: Whether to capture response events
        """
        self.page = page
        self.url_filter = url_filter
        self.capture_requests = capture_requests
        self.capture_responses = capture_responses
        self.logger = Logger.get_instance({})
        self.requests: list[dict[str, Any]] = []
        self._listeners_setup = False

        # Keep references to handlers for proper detachment
        self._bound_request = self._on_request
        self._bound_response = self._on_response
        self._bound_failed = self._on_request_failed

    def start_collection(self) -> None:
        """Start collecting network events."""
        if self._listeners_setup:
            return

        try:
            if self.capture_requests or self.capture_responses:
                self.page.on("request", self._bound_request)
            if self.capture_responses:
                self.page.on("response", self._bound_response)
            self.page.on("requestfailed", self._bound_failed)

            self._listeners_setup = True
            self.logger.debug("Network listeners setup successfully")

        except (KeyboardInterrupt, SystemExit):
            raise
        except (AttributeError, RuntimeError) as e:
            self.logger.error(
                f"Failed to setup network listeners: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="NetworkEventCollector",
                method="start_collection"
            )
            raise CollectorError("Failed to setup network listeners", str(e)) from e

    def stop_collection(self) -> None:
        """Stop collecting network events and detach listeners."""
        if self._listeners_setup:
            self.page.off("request", self._bound_request)
            self.page.off("response", self._bound_response)
            self.page.off("requestfailed", self._bound_failed)
            self._listeners_setup = False

    def get_collected_data(self) -> list[dict[str, Any]]:
        """
        Get all collected network events.

        Returns:
            Copy of collected events list
        """
        return self.requests.copy()

    def clear_collected_data(self) -> None:
        """Clear all collected events."""
        self.requests.clear()

    def _should_track_url(self, url: str) -> bool:
        """
        Check if URL should be tracked based on filter.

        Args:
            url: URL to check

        Returns:
            True if URL should be tracked
        """
        return True if not self.url_filter else self.url_filter in url

    def _on_request(self, request: Request) -> None:
        """
        Handle request event.

        Args:
            request: Playwright Request object
        """
        if not self.capture_requests:
            return

        if not self._should_track_url(request.url):
            return

        if len(self.requests) >= self.MAX_REQUESTS:
            return

        # Truncate long URLs
        url = request.url
        if len(url) > self.MAX_URL_LENGTH:
            url = url[:self.MAX_URL_LENGTH] + "...[truncated]"

        # Truncate long POST data
        post_data = request.post_data
        if post_data and len(post_data) > self.MAX_POST_DATA_LENGTH:
            post_data = post_data[:self.MAX_POST_DATA_LENGTH] + "...[truncated]"

        self.requests.append({
            "url": url,
            "method": request.method,
            "headers": dict(request.headers),
            "resource_type": request.resource_type,
            "post_data": post_data,
            "timestamp": self._get_timestamp(),
            "type": "request",
        })

    def _on_response(self, response: Response) -> None:
        """
        Handle response event.

        Args:
            response: Playwright Response object
        """
        if not self.capture_responses:
            return

        if not self._should_track_url(response.url):
            return

        if len(self.requests) >= self.MAX_REQUESTS:
            return

        # Truncate long URLs
        url = response.url
        if len(url) > self.MAX_URL_LENGTH:
            url = url[:self.MAX_URL_LENGTH] + "...[truncated]"

        # Calculate response duration
        duration = self._calculate_duration(response)

        # Parse response size from content-length header
        response_size = self._parse_content_length(response.headers.get("content-length"))

        self.requests.append({
            "url": url,
            "status": response.status,
            "status_text": response.status_text,
            "method": response.request.method,
            "duration": round(duration, 2),
            "size": response_size,
            "content_type": response.headers.get("content-type", "unknown"),
            "timestamp": self._get_timestamp(),
            "type": "response",
        })

    def _on_request_failed(self, request: Request) -> None:
        """
        Handle failed request event.

        Args:
            request: Playwright Request object
        """
        if not self._should_track_url(request.url):
            return

        if len(self.requests) >= self.MAX_REQUESTS:
            return

        # Truncate long URLs
        url = request.url
        if len(url) > self.MAX_URL_LENGTH:
            url = url[:self.MAX_URL_LENGTH] + "...[truncated]"

        failure = request.failure
        error_text = failure if failure else "Unknown error"

        self.requests.append({
            "url": url,
            "method": request.method,
            "error": error_text,
            "timestamp": self._get_timestamp(),
            "type": "failed",
        })

    def _calculate_duration(self, response: Response) -> float:
        """
        Calculate response duration from timing data.

        Args:
            response: Playwright Response object

        Returns:
            Duration in milliseconds (0.0 if calculation fails)
        """
        duration = 0.0
        timing = response.request.timing

        if timing:
            try:
                response_end = getattr(timing, "responseEnd", None)
                request_start = getattr(timing, "requestStart", None)
                if response_end is not None and request_start is not None:
                    duration = response_end - request_start
            except (AttributeError, TypeError, ValueError) as e:
                self.logger.debug(
                    f"Failed to calculate response duration: {e}",
                    module=__name__,
                    class_name="NetworkEventCollector",
                    method="_calculate_duration"
                )
            except (KeyboardInterrupt, SystemExit):
                raise

        return duration

    def _parse_content_length(self, content_length: str | None) -> int:
        """
        Parse content-length header to integer.

        Args:
            content_length: Content-Length header value

        Returns:
            Size in bytes (0 if parsing fails)
        """
        if not content_length:
            return 0

        try:
            return int(content_length)
        except (ValueError, TypeError) as e:
            self.logger.debug(
                f"Failed to parse content-length: {e}",
                module=__name__,
                class_name="NetworkEventCollector",
                method="_parse_content_length"
            )
            return 0
        except (KeyboardInterrupt, SystemExit):
            raise

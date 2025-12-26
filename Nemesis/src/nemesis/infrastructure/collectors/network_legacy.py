"""Network request and response collection """
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List

from playwright.sync_api import Page, Request, Response

from nemesis.domain.ports import ICollector
from nemesis.shared.exceptions import CollectorError
from nemesis.infrastructure.logging import Logger
from nemesis.utils import get_path_manager
from nemesis.utils.helpers.exception_helpers import ensure_directory_exists
from nemesis.utils.decorators.exception_handler import handle_exceptions
from .base_collector import BaseCollector


class NetworkCollector(ICollector, BaseCollector):
    """Collects network requests and responses implementing ICollector port."""

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
        self.page = page
        self.url_filter = url_filter
        self.capture_requests = capture_requests
        self.capture_responses = capture_responses
        self.logger = Logger.get_instance({})
        self.requests: list[dict[str, Any]] = []
        self._listeners_setup = False

        if self.capture_requests or self.capture_responses:
            self._setup_listeners()
        # Keep references to handlers for proper detachment
        self._bound_request = self._on_request
        self._bound_response = self._on_response
        self._bound_failed = self._on_request_failed

    def _setup_listeners(self) -> None:
        """Setup network event listeners."""
        if self._listeners_setup:
            return
        try:
            if self.capture_requests or self.capture_responses:
                self.page.on("request", self._on_request)
            if self.capture_responses:
                self.page.on("response", self._on_response)
            self.page.on("requestfailed", self._on_request_failed)
            self._listeners_setup = True
            self.logger.debug("Network listeners setup successfully")
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Playwright page event listener errors
            self.logger.error(f"Failed to setup network listeners: {e}", traceback=traceback.format_exc(), module=__name__, class_name="NetworkCollector", method="_setup_listeners")
            raise CollectorError("Failed to setup network listeners", str(e)) from e

    def _should_track_url(self, url: str) -> bool:
        """Check if URL should be tracked based on filter."""
        return True if not self.url_filter else self.url_filter in url

    def _on_request(self, request: Request) -> None:
        """Handle request event."""
        if not self.capture_requests:
            return

        if not self._should_track_url(request.url):
            return
        if len(self.requests) >= self.MAX_REQUESTS:
            return

        url = request.url
        if len(url) > self.MAX_URL_LENGTH:
            url = url[:self.MAX_URL_LENGTH] + "...[truncated]"

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
        """Handle response event."""
        if not self.capture_responses:
            return

        if not self._should_track_url(response.url):
            return
        if len(self.requests) >= self.MAX_REQUESTS:
            return

        url = response.url
        if len(url) > self.MAX_URL_LENGTH:
            url = url[:self.MAX_URL_LENGTH] + "...[truncated]"

        duration = 0.0
        timing = response.request.timing
        if timing:
            try:
                response_end = getattr(timing, "responseEnd", None)
                request_start = getattr(timing, "requestStart", None)
                if response_end is not None and request_start is not None:
                    duration = response_end - request_start
            except (AttributeError, TypeError, ValueError) as e:
                # Timing calculation errors - continue with 0 duration
                self.logger.debug(f"Failed to calculate response duration: {e}", module=__name__, class_name="NetworkCollector", method="_on_response")
            except KeyboardInterrupt:
                raise
            except SystemExit:
                raise

        response_size = 0
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                response_size = int(content_length)
            except (ValueError, TypeError) as e:
                # Content length parsing errors - continue with 0 size
                self.logger.debug(f"Failed to parse content-length: {e}", module=__name__, class_name="NetworkCollector", method="_on_response")
            except KeyboardInterrupt:
                raise
            except SystemExit:
                raise

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
        """Handle failed request event."""
        if not self._should_track_url(request.url):
            return
        if len(self.requests) >= self.MAX_REQUESTS:
            return

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

    def get_metrics(self) -> dict[str, Any]:
        """Get network metrics summary."""
        requests = [r for r in self.requests if r["type"] == "request"]
        responses = [r for r in self.requests if r["type"] == "response"]
        failed = [r for r in self.requests if r["type"] == "failed"]

        status_codes: dict[int, int] = {}
        for r in responses:
            status = r.get("status", 0)
            status_codes[status] = status_codes.get(status, 0) + 1

        durations = [r.get("duration", 0) for r in responses if r.get("duration")]
        avg_duration = sum(durations) / len(durations) if durations else 0
        total_size = sum(r.get("size", 0) for r in responses)

        return {
            "total_requests": len(requests),
            "total_responses": len(responses),
            "total_failed": len(failed),
            "status_codes": status_codes,
            "avg_duration_ms": round(avg_duration, 2),
            "total_size_bytes": total_size,
            "requests": self.requests.copy(),
        }

    def export_as_har(self) -> dict[str, Any]:
        """
        Export network data as HAR (HTTP Archive) 1.2 format.

        HAR format is compatible with Chrome DevTools, Firefox DevTools,
        and other network analysis tools.

        Returns:
            HAR 1.2 formatted dict

        Reference: http://www.softwareishard.com/blog/har-12-spec/
        """
        # Combine requests with their responses
        # Create a map of URL -> request data
        request_map: dict[str, dict] = {}
        for req in self.requests:
            if req["type"] == "request":
                request_map[req["url"]] = req

        # Build HAR entries
        entries = []
        for item in self.requests:
            if item["type"] == "response":
                url = item["url"]
                request_data = request_map.get(url, {})

                # Build HAR entry
                entry = {
                    "startedDateTime": self._timestamp_to_iso(item.get("timestamp", 0)),
                    "time": item.get("duration", 0),
                    "request": {
                        "method": item.get("method", "GET"),
                        "url": url,
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": self._dict_to_har_headers(request_data.get("headers", {})),
                        "queryString": [],
                        "postData": self._create_post_data(request_data.get("post_data")),
                        "headersSize": -1,
                        "bodySize": len(request_data.get("post_data", "")) if request_data.get("post_data") else 0,
                    },
                    "response": {
                        "status": item.get("status", 0),
                        "statusText": item.get("status_text", ""),
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [],
                        "content": {
                            "size": item.get("size", 0),
                            "mimeType": item.get("content_type", ""),
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": item.get("size", 0),
                    },
                    "cache": {},
                    "timings": {
                        "blocked": -1,
                        "dns": -1,
                        "connect": -1,
                        "send": 0,
                        "wait": item.get("duration", 0),
                        "receive": 0,
                        "ssl": -1,
                    },
                }
                entries.append(entry)

            elif item["type"] == "failed":
                # Add failed requests as entries with error status
                entry = {
                    "startedDateTime": self._timestamp_to_iso(item.get("timestamp", 0)),
                    "time": 0,
                    "request": {
                        "method": item.get("method", "GET"),
                        "url": item.get("url", ""),
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [],
                        "queryString": [],
                        "headersSize": -1,
                        "bodySize": 0,
                    },
                    "response": {
                        "status": 0,
                        "statusText": f"Failed: {item.get('error', 'Unknown error')}",
                        "httpVersion": "HTTP/1.1",
                        "cookies": [],
                        "headers": [],
                        "content": {
                            "size": 0,
                            "mimeType": "",
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": 0,
                    },
                    "cache": {},
                    "timings": {
                        "blocked": -1,
                        "dns": -1,
                        "connect": -1,
                        "send": -1,
                        "wait": -1,
                        "receive": -1,
                        "ssl": -1,
                    },
                }
                entries.append(entry)

        # Build HAR structure
        har = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "Nemesis Test Framework",
                    "version": "1.0.0",
                },
                "browser": {
                    "name": "Playwright",
                    "version": "1.0.0",
                },
                "pages": [],
                "entries": entries,
            }
        }

        return har

    def _timestamp_to_iso(self, timestamp: float) -> str:
        """
        Convert timestamp to ISO 8601 format for HAR.

        Args:
            timestamp: Timestamp in milliseconds

        Returns:
            ISO 8601 formatted datetime string
        """
        from datetime import datetime, timezone
        try:
            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            return dt.isoformat()
        except (ValueError, OSError):
            # Fallback to current time if timestamp is invalid
            return datetime.now(timezone.utc).isoformat()

    def _dict_to_har_headers(self, headers: dict) -> list[dict]:
        """
        Convert headers dict to HAR headers format.

        Args:
            headers: Dict of header name -> value

        Returns:
            List of {name, value} dicts
        """
        return [{"name": name, "value": value} for name, value in headers.items()]

    def _create_post_data(self, post_data: str | None) -> dict | None:
        """
        Create HAR postData object.

        Args:
            post_data: POST data string

        Returns:
            HAR postData object or None
        """
        if not post_data:
            return None

        return {
            "mimeType": "application/x-www-form-urlencoded",
            "text": post_data,
            "params": [],
        }

    def save_metrics(self, execution_id: str, _scenario_name: str) -> Path:
        """
        Save network metrics to JSON and HAR formats.

        Saves two files:
        1. network_metric.json - Custom format with Nemesis metrics
        2. network.har - Standard HAR 1.2 format (importable to Chrome DevTools)

        Returns:
            Path to JSON metrics file
        """
        try:
            # Use PathHelper for centralized path management
            try:
                path_manager = get_path_manager()
                json_file_path = path_manager.get_attachment_path(execution_id, "network", "network_metric.json")
                har_file_path = path_manager.get_attachment_path(execution_id, "network", "network.har")
            except (AttributeError, KeyError, RuntimeError) as e:
                # PathHelper initialization errors - fallback to original logic
                self.logger.debug(f"PathHelper failed, using fallback path: {e}", traceback=traceback.format_exc(), module=__name__, class_name="NetworkCollector", method="save_metrics", execution_id=execution_id)
                json_file_path = Path(f"reports/{execution_id}/network/network_metric.json")
                har_file_path = Path(f"reports/{execution_id}/network/network.har")
                ensure_directory_exists(json_file_path, execution_id)
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
                raise

            # Save custom JSON format
            metrics = self.get_metrics()
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Network metrics (JSON) saved: {json_file_path} ({metrics['total_requests']} requests)")

            # Save HAR format
            try:
                har_data = self.export_as_har()
                with open(har_file_path, "w", encoding="utf-8") as f:
                    json.dump(har_data, f, indent=2, ensure_ascii=False)

                self.logger.info(f"Network metrics (HAR) saved: {har_file_path} ({len(har_data['log']['entries'])} entries)")
            except Exception as har_error:  # pylint: disable=broad-exception-caught
                # HAR export is supplementary - don't fail if it errors
                self.logger.warning(f"Failed to save HAR format: {har_error}")

            return json_file_path

        except (OSError, IOError, PermissionError) as e:
            # File system errors
            self.logger.error(f"Failed to save network metrics: {e}", traceback=traceback.format_exc(), module=__name__, class_name="NetworkCollector", method="save_metrics", execution_id=execution_id)
            raise CollectorError("Failed to save network metrics", str(e)) from e
        except (TypeError, ValueError) as e:
            # JSON serialization errors - TypeError for non-serializable objects, ValueError for invalid values
            self.logger.error(f"Failed to serialize network metrics: {e}", traceback=traceback.format_exc(), module=__name__, class_name="NetworkCollector", method="save_metrics", execution_id=execution_id)
            raise CollectorError("Failed to save network metrics", str(e)) from e
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            # Always re-raise these to allow proper program termination
            # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
            raise

    def _cleanup_listeners(self) -> None:
        """Clean up network listeners."""
        if self._listeners_setup:
            # Detach to prevent post-shutdown emissions
            self.page.off("request", self._bound_request)
            self.page.off("response", self._bound_response)
            self.page.off("requestfailed", self._bound_failed)
            self._listeners_setup = False

    @handle_exceptions(
        log_level="debug",
        catch_exceptions=(AttributeError, RuntimeError),
        message_template="Error detaching network listeners during dispose: {error}"
    )
    def dispose(self) -> None:
        """Detach all network listeners explicitly."""
        if self._listeners_setup:
            self.page.off("request", self._bound_request)
            self.page.off("response", self._bound_response)
            self.page.off("requestfailed", self._bound_failed)
        self._listeners_setup = False

    # ICollector interface implementation
    def start(self) -> None:
        """Start collecting network data."""
        if not self._listeners_setup:
            self._setup_listeners()

    def stop(self) -> None:
        """Stop collecting network data."""
        self._cleanup_listeners()

    def get_collected_data(self) -> List[Dict[str, Any]]:
        """Get collected network requests/responses."""
        return self.requests.copy()

    def save_collected_data(
        self,
        execution_id: str,
        output_dir: Path,
        scenario_name: str = ""
    ) -> Path:
        """Save collected data to file."""
        return self.save_metrics(execution_id, scenario_name)

    def clear(self) -> None:
        """Clear collected data."""
        self.requests.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return self.get_metrics()

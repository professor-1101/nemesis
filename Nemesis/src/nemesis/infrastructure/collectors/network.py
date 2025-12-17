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

    def save_metrics(self, execution_id: str, _scenario_name: str) -> Path:
        """Save network metrics to JSON."""
        try:
            # Use PathManager for centralized path management
            try:
                path_manager = get_path_manager()
                file_path = path_manager.get_attachment_path(execution_id, "network", "network_metric.json")
            except (AttributeError, KeyError, RuntimeError) as e:
                # PathManager initialization errors - fallback to original logic
                self.logger.debug(f"PathManager failed, using fallback path: {e}", traceback=traceback.format_exc(), module=__name__, class_name="NetworkCollector", method="save_metrics", execution_id=execution_id)
                file_path = Path(f"reports/{execution_id}/network/network_metric.json")
                ensure_directory_exists(file_path, execution_id)
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # NOTE: Always re-raise KeyboardInterrupt and SystemExit to allow proper program termination
                raise

            metrics = self.get_metrics()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Network metrics saved: {file_path} ({metrics['total_requests']} requests)")
            return file_path

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

    def dispose(self) -> None:
        """Detach all network listeners explicitly."""
        try:
            if self._listeners_setup:
                self.page.off("request", self._bound_request)
                self.page.off("response", self._bound_response)
                self.page.off("requestfailed", self._bound_failed)
        except (AttributeError, RuntimeError) as e:
            # Playwright page event listener errors - ignore during cleanup
            self.logger.debug(f"Error detaching network listeners during dispose: {e}", module=__name__, class_name="NetworkCollector", method="dispose")
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
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

"""HAR (HTTP Archive) format export module.

Exports network data to HAR 1.2 format compatible with Chrome DevTools,
Firefox DevTools, and other network analysis tools.

Reference: http://www.softwareishard.com/blog/har-12-spec/
"""
from datetime import datetime, timezone
from typing import Any


class HARExporter:
    """
    Exports network request/response data to HAR 1.2 format.

    Responsibilities:
    - Convert network data to HAR 1.2 specification
    - Format timestamps to ISO 8601
    - Structure headers in HAR format
    - Handle failed requests appropriately

    HAR files can be imported into Chrome DevTools Network panel for analysis.
    """

    VERSION = "1.2"
    FRAMEWORK_NAME = "Nemesis Test Framework"
    FRAMEWORK_VERSION = "1.0.0"
    BROWSER_NAME = "Playwright"
    BROWSER_VERSION = "1.0.0"

    def export(self, requests_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Export network data as HAR (HTTP Archive) 1.2 format.

        Args:
            requests_data: List of network request/response/failed events

        Returns:
            HAR 1.2 formatted dictionary

        Example:
            >>> exporter = HARExporter()
            >>> har_data = exporter.export(network_requests)
            >>> # Save to file or import to Chrome DevTools
        """
        # Combine requests with their responses
        request_map = self._build_request_map(requests_data)

        # Build HAR entries
        entries = []
        for item in requests_data:
            if item["type"] == "response":
                entry = self._create_response_entry(item, request_map)
                entries.append(entry)
            elif item["type"] == "failed":
                entry = self._create_failed_entry(item)
                entries.append(entry)

        # Build HAR structure
        return {
            "log": {
                "version": self.VERSION,
                "creator": {
                    "name": self.FRAMEWORK_NAME,
                    "version": self.FRAMEWORK_VERSION,
                },
                "browser": {
                    "name": self.BROWSER_NAME,
                    "version": self.BROWSER_VERSION,
                },
                "pages": [],
                "entries": entries,
            }
        }

    def _build_request_map(self, requests_data: list[dict[str, Any]]) -> dict[str, dict]:
        """
        Create a map of URL -> request data for quick lookup.

        Args:
            requests_data: List of network events

        Returns:
            Dictionary mapping URL to request data
        """
        request_map: dict[str, dict] = {}
        for req in requests_data:
            if req["type"] == "request":
                request_map[req["url"]] = req
        return request_map

    def _create_response_entry(self, response_item: dict[str, Any], request_map: dict[str, dict]) -> dict[str, Any]:
        """
        Create HAR entry for successful response.

        Args:
            response_item: Response event data
            request_map: Map of URL to request data

        Returns:
            HAR entry dictionary
        """
        url = response_item["url"]
        request_data = request_map.get(url, {})

        return {
            "startedDateTime": self._timestamp_to_iso(response_item.get("timestamp", 0)),
            "time": response_item.get("duration", 0),
            "request": {
                "method": response_item.get("method", "GET"),
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
                "status": response_item.get("status", 0),
                "statusText": response_item.get("status_text", ""),
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": [],
                "content": {
                    "size": response_item.get("size", 0),
                    "mimeType": response_item.get("content_type", ""),
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": response_item.get("size", 0),
            },
            "cache": {},
            "timings": {
                "blocked": -1,
                "dns": -1,
                "connect": -1,
                "send": 0,
                "wait": response_item.get("duration", 0),
                "receive": 0,
                "ssl": -1,
            },
        }

    def _create_failed_entry(self, failed_item: dict[str, Any]) -> dict[str, Any]:
        """
        Create HAR entry for failed request.

        Args:
            failed_item: Failed request event data

        Returns:
            HAR entry dictionary with error status
        """
        return {
            "startedDateTime": self._timestamp_to_iso(failed_item.get("timestamp", 0)),
            "time": 0,
            "request": {
                "method": failed_item.get("method", "GET"),
                "url": failed_item.get("url", ""),
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": [],
                "queryString": [],
                "headersSize": -1,
                "bodySize": 0,
            },
            "response": {
                "status": 0,
                "statusText": f"Failed: {failed_item.get('error', 'Unknown error')}",
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

    def _timestamp_to_iso(self, timestamp: float) -> str:
        """
        Convert timestamp to ISO 8601 format for HAR.

        Args:
            timestamp: Timestamp in milliseconds

        Returns:
            ISO 8601 formatted datetime string
        """
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

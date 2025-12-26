"""Network metrics calculation module.

Calculates aggregated metrics from network request/response data.
Optimized for single-pass calculation (O(n) instead of O(5n)).
"""
from typing import Any


class NetworkMetricsCalculator:
    """
    Calculates network metrics from collected request/response data.

    Responsibilities:
    - Aggregate request/response counts by type
    - Calculate status code distributions
    - Compute duration statistics
    - Sum total data transfer sizes

    Optimized for single-pass calculation to avoid multiple iterations.
    """

    def calculate_metrics(self, requests_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Calculate comprehensive network metrics from request/response data.

        Uses single-pass algorithm (O(n)) instead of multiple passes (O(5n)).

        Args:
            requests_data: List of network request/response/failed events

        Returns:
            Dictionary containing:
            - total_requests: Count of request events
            - total_responses: Count of response events
            - total_failed: Count of failed events
            - status_codes: Distribution of HTTP status codes
            - avg_duration_ms: Average response duration in milliseconds
            - total_size_bytes: Total data transferred in bytes
            - requests: Copy of original data

        Example:
            >>> calculator = NetworkMetricsCalculator()
            >>> metrics = calculator.calculate_metrics(network_data)
            >>> print(f"Average duration: {metrics['avg_duration_ms']}ms")
        """
        # Initialize counters and accumulators
        requests = []
        responses = []
        failed = []
        status_codes: dict[int, int] = {}
        durations = []
        total_size = 0

        # Single pass through all data - O(n) complexity
        for item in requests_data:
            item_type = item.get("type")

            if item_type == "request":
                requests.append(item)

            elif item_type == "response":
                responses.append(item)

                # Aggregate status codes
                status = item.get("status", 0)
                if status:
                    status_codes[status] = status_codes.get(status, 0) + 1

                # Collect durations for average calculation
                duration = item.get("duration", 0)
                if duration:
                    durations.append(duration)

                # Sum total size
                size = item.get("size", 0)
                if size:
                    total_size += size

            elif item_type == "failed":
                failed.append(item)

        # Calculate average duration
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_requests": len(requests),
            "total_responses": len(responses),
            "total_failed": len(failed),
            "status_codes": status_codes,
            "avg_duration_ms": round(avg_duration, 2),
            "total_size_bytes": total_size,
            "requests": requests_data.copy(),
        }

    def get_status_code_summary(self, status_codes: dict[int, int]) -> dict[str, int]:
        """
        Categorize status codes into groups.

        Args:
            status_codes: Dict mapping status code to count

        Returns:
            Dictionary with success/client_error/server_error counts
        """
        summary = {
            "success": 0,       # 2xx
            "redirect": 0,      # 3xx
            "client_error": 0,  # 4xx
            "server_error": 0,  # 5xx
        }

        for code, count in status_codes.items():
            if 200 <= code < 300:
                summary["success"] += count
            elif 300 <= code < 400:
                summary["redirect"] += count
            elif 400 <= code < 500:
                summary["client_error"] += count
            elif 500 <= code < 600:
                summary["server_error"] += count

        return summary

    def calculate_percentiles(self, durations: list[float], percentiles: list[int] = None) -> dict[str, float]:
        """
        Calculate duration percentiles (p50, p75, p90, p95, p99).

        Args:
            durations: List of response durations in milliseconds
            percentiles: List of percentile values to calculate (default: [50, 75, 90, 95, 99])

        Returns:
            Dictionary mapping percentile to duration value
        """
        if not durations:
            return {}

        if percentiles is None:
            percentiles = [50, 75, 90, 95, 99]

        sorted_durations = sorted(durations)
        results = {}

        for p in percentiles:
            index = int(len(sorted_durations) * p / 100)
            if index >= len(sorted_durations):
                index = len(sorted_durations) - 1
            results[f"p{p}"] = round(sorted_durations[index], 2)

        return results

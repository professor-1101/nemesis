"""SigNoz Shipper - Ships logs to SigNoz observability platform

This adapter implements ILogShipper for SigNoz integration.
"""

import json
import time
from typing import Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nemesis.domain.ports import ILogShipper
from nemesis.infrastructure.logging import Logger


class SigNozShipper(ILogShipper):
    """
    Adapter: SigNoz Log Shipper

    Ships logs to SigNoz observability platform with:
    - Batch shipping for performance
    - Retry logic for reliability
    - Backpressure handling

    Clean Architecture:
    - Implements ILogShipper interface
    - Infrastructure layer adapter
    - Domain is unaware of SigNoz
    """

    def __init__(
        self,
        endpoint: str,
        service_name: str,
        batch_size: int = 100,
        retry_attempts: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize SigNoz shipper

        Args:
            endpoint: SigNoz logs endpoint (e.g., http://signoz:4317/v1/logs)
            service_name: Service name for log attribution
            batch_size: Number of logs to batch before sending
            retry_attempts: Number of retry attempts on failure
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.service_name = service_name
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.timeout = timeout

        # Batch buffer
        self._batch: List[Dict[str, Any]] = []

        # Setup HTTP session with retries
        self._session = requests.Session()
        retry_strategy = Retry(
            total=retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def ship(self, log_entry: Dict[str, Any]) -> bool:
        """
        Ship a single log entry

        Args:
            log_entry: Log entry dictionary

        Returns:
            True if shipped successfully
        """
        # Add to batch
        self._batch.append(self._enrich_log(log_entry))

        # Ship if batch is full
        if len(self._batch) >= self.batch_size:
            return self._flush_batch()

        return True

    def ship_batch(self, log_entries: List[Dict[str, Any]]) -> bool:
        """
        Ship multiple log entries in batch

        Args:
            log_entries: List of log entries

        Returns:
            True if all shipped successfully
        """
        # Enrich all logs
        enriched_logs = [self._enrich_log(log) for log in log_entries]

        # Ship in batches
        for i in range(0, len(enriched_logs), self.batch_size):
            batch = enriched_logs[i:i + self.batch_size]
            if not self._ship_to_signoz(batch):
                return False

        return True

    def flush(self) -> None:
        """Flush any pending log entries"""
        if self._batch:
            self._flush_batch()

    def close(self) -> None:
        """Close shipper and cleanup resources"""
        self.flush()
        self._session.close()

    def get_channel_name(self) -> str:
        """Get channel name"""
        return "signoz"

    def is_healthy(self) -> bool:
        """Check if shipper is healthy"""
        try:
            # Try a simple HEAD request to check connectivity
            response = self._session.head(self.endpoint, timeout=5)
            return response.status_code < 500
        except Exception:
            return False

    def _enrich_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich log entry with SigNoz-specific fields

        Args:
            log_entry: Original log entry

        Returns:
            Enriched log entry
        """
        enriched = log_entry.copy()

        # Add service name if not present
        if "service_name" not in enriched:
            enriched["service_name"] = self.service_name

        # Ensure timestamp is present
        if "timestamp" not in enriched:
            enriched["timestamp"] = time.time()

        # Add SigNoz-specific fields
        enriched["attributes"] = enriched.get("attributes", {})
        enriched["attributes"]["service.name"] = self.service_name

        return enriched

    def _flush_batch(self) -> bool:
        """Flush current batch"""
        if not self._batch:
            return True

        result = self._ship_to_signoz(self._batch)
        self._batch = []
        return result

    def _ship_to_signoz(self, logs: List[Dict[str, Any]]) -> bool:
        """
        Ship logs to SigNoz

        Args:
            logs: List of log entries

        Returns:
            True if successful
        """
        try:
            # Prepare payload for SigNoz
            payload = {
                "resourceLogs": [
                    {
                        "resource": {
                            "attributes": [
                                {"key": "service.name", "value": {"stringValue": self.service_name}}
                            ]
                        },
                        "scopeLogs": [
                            {
                                "scope": {"name": "nemesis"},
                                "logRecords": [self._convert_to_otlp_format(log) for log in logs]
                            }
                        ]
                    }
                ]
            }

            # Send to SigNoz
            response = self._session.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )

            response.raise_for_status()
            return True

        except Exception as e:
            Logger.get_instance({}).info(f"[SigNozShipper] Failed to ship logs: {e}")
            return False

    def _convert_to_otlp_format(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert log to OpenTelemetry Log Protocol format

        Args:
            log: Log entry

        Returns:
            OTLP-formatted log
        """
        return {
            "timeUnixNano": str(int(log.get("timestamp", time.time()) * 1e9)),
            "severityText": log.get("level", "INFO"),
            "body": {"stringValue": log.get("message", "")},
            "attributes": [
                {"key": k, "value": {"stringValue": str(v)}}
                for k, v in log.get("context", {}).items()
            ],
        }

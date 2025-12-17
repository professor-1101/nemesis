"""Unit tests for Collector implementations"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from nemesis.collectors.console import ConsoleCollector
from nemesis.collectors.network import NetworkCollector


class TestConsoleCollector:
    """Tests for ConsoleCollector implementing ICollector"""

    @pytest.fixture
    def mock_page(self):
        """Create mock Playwright page"""
        page = Mock()
        page.on = Mock()
        page.off = Mock()
        return page

    @pytest.fixture
    def collector(self, mock_page):
        """Create console collector"""
        return ConsoleCollector(page=mock_page, filter_levels=["error", "warning"])

    def test_initialization(self, collector, mock_page):
        """Test collector initialization"""
        assert collector.page == mock_page
        assert collector.filter_levels == ["error", "warning"]
        assert collector.logs == []
        assert collector._listener_active is True

    def test_start_activates_listener(self, collector):
        """Test start method activates listener"""
        collector._listener_active = False
        collector.start()
        assert collector._listener_active is True

    def test_stop_deactivates_listener(self, collector):
        """Test stop method deactivates listener"""
        collector.stop()
        assert collector._listener_active is False

    def test_get_collected_data_returns_copy(self, collector):
        """Test get_collected_data returns copy of logs"""
        # Add some test data
        collector.logs = [
            {"type": "error", "text": "Test error", "timestamp": 1000}
        ]

        data = collector.get_collected_data()

        assert len(data) == 1
        assert data[0]["type"] == "error"
        # Verify it's a copy
        data.append({"type": "warning", "text": "New warning"})
        assert len(collector.logs) == 1

    def test_clear_empties_logs(self, collector):
        """Test clear method empties logs"""
        collector.logs = [
            {"type": "error", "text": "Test error"}
        ]

        collector.clear()

        assert len(collector.logs) == 0

    def test_get_summary_returns_stats(self, collector):
        """Test get_summary returns statistics"""
        collector.logs = [
            {"type": "error", "text": "Error 1"},
            {"type": "error", "text": "Error 2"},
            {"type": "warning", "text": "Warning 1"},
        ]

        summary = collector.get_summary()

        assert summary["error"] == 2
        assert summary["warning"] == 1

    def test_validate_filter_levels_with_valid_levels(self, mock_page):
        """Test filter level validation with valid levels"""
        collector = ConsoleCollector(
            page=mock_page,
            filter_levels=["error", "WARNING", "INFO"]
        )

        assert "error" in collector.filter_levels
        assert "warning" in collector.filter_levels
        assert "info" in collector.filter_levels

    def test_validate_filter_levels_with_defaults(self, mock_page):
        """Test filter level defaults"""
        collector = ConsoleCollector(page=mock_page, filter_levels=None)

        assert collector.filter_levels == ["error", "warning"]

    def test_get_errors_filters_correctly(self, collector):
        """Test get_errors returns only error logs"""
        collector.logs = [
            {"type": "error", "text": "Error 1"},
            {"type": "warning", "text": "Warning 1"},
            {"type": "error", "text": "Error 2"},
        ]

        errors = collector.get_errors()

        assert len(errors) == 2
        assert all(log["type"] == "error" for log in errors)

    def test_get_warnings_filters_correctly(self, collector):
        """Test get_warnings returns only warning logs"""
        collector.logs = [
            {"type": "error", "text": "Error 1"},
            {"type": "warning", "text": "Warning 1"},
            {"type": "warning", "text": "Warning 2"},
        ]

        warnings = collector.get_warnings()

        assert len(warnings) == 2
        assert all(log["type"] == "warning" for log in warnings)


class TestNetworkCollector:
    """Tests for NetworkCollector implementing ICollector"""

    @pytest.fixture
    def mock_page(self):
        """Create mock Playwright page"""
        page = Mock()
        page.on = Mock()
        page.off = Mock()
        return page

    @pytest.fixture
    def collector(self, mock_page):
        """Create network collector"""
        return NetworkCollector(
            page=mock_page,
            url_filter=None,
            capture_requests=True,
            capture_responses=True
        )

    def test_initialization(self, collector, mock_page):
        """Test collector initialization"""
        assert collector.page == mock_page
        assert collector.capture_requests is True
        assert collector.capture_responses is True
        assert collector.requests == []

    def test_start_activates_listeners(self, collector):
        """Test start method activates listeners"""
        collector._listeners_setup = False
        collector.start()
        assert collector._listeners_setup is True

    def test_stop_deactivates_listeners(self, collector):
        """Test stop method deactivates listeners"""
        collector.stop()
        assert collector._listeners_setup is False

    def test_get_collected_data_returns_copy(self, collector):
        """Test get_collected_data returns copy of requests"""
        collector.requests = [
            {"url": "https://example.com", "type": "request"}
        ]

        data = collector.get_collected_data()

        assert len(data) == 1
        assert data[0]["url"] == "https://example.com"
        # Verify it's a copy
        data.append({"url": "https://test.com"})
        assert len(collector.requests) == 1

    def test_clear_empties_requests(self, collector):
        """Test clear method empties requests"""
        collector.requests = [
            {"url": "https://example.com", "type": "request"}
        ]

        collector.clear()

        assert len(collector.requests) == 0

    def test_get_summary_returns_metrics(self, collector):
        """Test get_summary returns network metrics"""
        collector.requests = [
            {"url": "https://api.com/users", "type": "request", "method": "GET"},
            {"url": "https://api.com/users", "type": "response", "status": 200, "duration": 150},
            {"url": "https://api.com/posts", "type": "failed", "error": "timeout"},
        ]

        summary = collector.get_summary()

        assert summary["total_requests"] == 1
        assert summary["total_responses"] == 1
        assert summary["total_failed"] == 1
        assert 200 in summary["status_codes"]

    def test_should_track_url_with_no_filter(self, collector):
        """Test URL tracking with no filter"""
        assert collector._should_track_url("https://example.com") is True
        assert collector._should_track_url("https://test.com") is True

    def test_should_track_url_with_filter(self, mock_page):
        """Test URL tracking with filter"""
        collector = NetworkCollector(
            page=mock_page,
            url_filter="api.example.com"
        )

        assert collector._should_track_url("https://api.example.com/users") is True
        assert collector._should_track_url("https://other.com/data") is False

    def test_get_metrics_calculates_averages(self, collector):
        """Test get_metrics calculates average duration"""
        collector.requests = [
            {"type": "response", "duration": 100, "size": 1000, "status": 200},
            {"type": "response", "duration": 200, "size": 2000, "status": 200},
            {"type": "response", "duration": 300, "size": 3000, "status": 404},
        ]

        metrics = collector.get_metrics()

        assert metrics["avg_duration_ms"] == 200.0
        assert metrics["total_size_bytes"] == 6000
        assert metrics["status_codes"][200] == 2
        assert metrics["status_codes"][404] == 1

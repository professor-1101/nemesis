"""E2E tests for browser driver implementation"""

import pytest
from unittest.mock import Mock, patch

from nemesis.infrastructure import PlaywrightBrowserDriver


class TestPlaywrightBrowserDriverE2E:
    """End-to-end tests for PlaywrightBrowserDriver"""

    @pytest.fixture
    def mock_playwright(self):
        """Mock Playwright to avoid actual browser launch"""
        with patch('nemesis.infrastructure.browser.playwright_adapter.sync_playwright') as mock_pw:
            # Setup mock chain
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_context = Mock()
            mock_page = Mock()

            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            mock_browser.contexts.return_value = [mock_context]

            mock_playwright_instance.__enter__ = Mock(return_value=mock_playwright_instance)
            mock_playwright_instance.__exit__ = Mock(return_value=False)

            mock_pw.return_value = mock_playwright_instance

            yield mock_playwright_instance, mock_browser, mock_page

    def test_driver_launch_and_close(self, mock_playwright):
        """Test browser driver launch and close lifecycle"""
        mock_pw_instance, mock_browser, mock_page = mock_playwright

        driver = PlaywrightBrowserDriver()

        # Launch browser
        browser = driver.launch(headless=True)

        # Verify browser was launched
        assert browser is not None
        assert driver.is_running()

        # Close browser
        driver.close()

        # Verify cleanup
        assert not driver.is_running()

    def test_driver_browser_type(self, mock_playwright):
        """Test getting browser type"""
        driver = PlaywrightBrowserDriver()
        driver.launch(headless=True)

        browser_type = driver.get_browser_type()
        assert browser_type == "chromium"

        driver.close()

    def test_driver_create_context(self, mock_playwright):
        """Test creating browser context"""
        mock_pw_instance, mock_browser, mock_page = mock_playwright

        driver = PlaywrightBrowserDriver()
        browser = driver.launch(headless=True)

        # Create context
        context = driver.create_context(browser, record_video=False, record_har=False)

        # Verify context was created
        assert context is not None

        driver.close()

    def test_driver_multiple_launches(self, mock_playwright):
        """Test launching browser multiple times"""
        driver = PlaywrightBrowserDriver()

        # First launch
        browser1 = driver.launch(headless=True)
        assert driver.is_running()
        driver.close()

        # Second launch
        browser2 = driver.launch(headless=False)
        assert driver.is_running()
        driver.close()

        assert not driver.is_running()

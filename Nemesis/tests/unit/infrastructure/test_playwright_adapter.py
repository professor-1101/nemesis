"""Unit tests for PlaywrightBrowserDriver"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from nemesis.infrastructure.browser.playwright_adapter import (
    PlaywrightBrowserDriver,
    PlaywrightBrowserAdapter,
    PlaywrightPageAdapter
)


class TestPlaywrightPageAdapter:
    """Tests for PlaywrightPageAdapter"""

    @pytest.fixture
    def mock_playwright_page(self):
        """Create mock Playwright page"""
        page = Mock()
        page.text_content.return_value = "Test content"
        page.is_visible.return_value = True
        page.screenshot.return_value = b"screenshot_bytes"
        page.evaluate.return_value = {"result": "ok"}
        return page

    @pytest.fixture
    def page_adapter(self, mock_playwright_page):
        """Create page adapter"""
        return PlaywrightPageAdapter(mock_playwright_page)

    def test_goto(self, page_adapter, mock_playwright_page):
        """Test navigation"""
        page_adapter.goto("https://example.com")
        mock_playwright_page.goto.assert_called_once_with("https://example.com")

    def test_click(self, page_adapter, mock_playwright_page):
        """Test clicking element"""
        page_adapter.click("#button")
        mock_playwright_page.click.assert_called_once_with("#button")

    def test_fill(self, page_adapter, mock_playwright_page):
        """Test filling input"""
        page_adapter.fill("#input", "test value")
        mock_playwright_page.fill.assert_called_once_with("#input", "test value")

    def test_get_text(self, page_adapter, mock_playwright_page):
        """Test getting text content"""
        text = page_adapter.get_text("#element")
        assert text == "Test content"
        mock_playwright_page.text_content.assert_called_once_with("#element")

    def test_get_text_returns_empty_when_none(self, page_adapter, mock_playwright_page):
        """Test get_text returns empty string when None"""
        mock_playwright_page.text_content.return_value = None
        text = page_adapter.get_text("#element")
        assert text == ""

    def test_is_visible(self, page_adapter, mock_playwright_page):
        """Test visibility check"""
        assert page_adapter.is_visible("#element") is True
        mock_playwright_page.is_visible.assert_called_once_with("#element")

    def test_screenshot(self, page_adapter, mock_playwright_page):
        """Test screenshot capture"""
        screenshot = page_adapter.screenshot()
        assert screenshot == b"screenshot_bytes"
        mock_playwright_page.screenshot.assert_called_once()

    def test_evaluate(self, page_adapter, mock_playwright_page):
        """Test JavaScript evaluation"""
        result = page_adapter.evaluate("return 1 + 1;")
        assert result == {"result": "ok"}
        mock_playwright_page.evaluate.assert_called_once_with("return 1 + 1;")

    def test_close(self, page_adapter, mock_playwright_page):
        """Test closing page"""
        page_adapter.close()
        mock_playwright_page.close.assert_called_once()

    def test_playwright_page_property(self, page_adapter, mock_playwright_page):
        """Test accessing underlying Playwright page"""
        assert page_adapter.playwright_page == mock_playwright_page


class TestPlaywrightBrowserAdapter:
    """Tests for PlaywrightBrowserAdapter"""

    @pytest.fixture
    def mock_playwright_browser(self):
        """Create mock Playwright browser"""
        browser = Mock()
        context = Mock()
        page = Mock()

        browser.new_context.return_value = context
        context.new_page.return_value = page
        browser.contexts = []

        return browser

    @pytest.fixture
    def browser_adapter(self, mock_playwright_browser):
        """Create browser adapter"""
        return PlaywrightBrowserAdapter(mock_playwright_browser)

    def test_new_page_creates_context(self, browser_adapter, mock_playwright_browser):
        """Test new page creation"""
        page = browser_adapter.new_page()

        assert isinstance(page, PlaywrightPageAdapter)
        mock_playwright_browser.new_context.assert_called_once()

    def test_new_page_reuses_context(self, browser_adapter, mock_playwright_browser):
        """Test new page reuses existing context"""
        page1 = browser_adapter.new_page()
        page2 = browser_adapter.new_page()

        # Context should only be created once
        assert mock_playwright_browser.new_context.call_count == 1

    def test_close(self, browser_adapter, mock_playwright_browser):
        """Test closing browser"""
        # Create context first
        browser_adapter.new_page()

        browser_adapter.close()

        browser_adapter._context.close.assert_called_once()
        mock_playwright_browser.close.assert_called_once()

    def test_contexts_property(self, browser_adapter, mock_playwright_browser):
        """Test contexts property"""
        mock_playwright_browser.contexts = ["context1", "context2"]
        assert browser_adapter.contexts() == ["context1", "context2"]


class TestPlaywrightBrowserDriver:
    """Tests for PlaywrightBrowserDriver"""

    def test_initialization(self):
        """Test driver initialization"""
        driver = PlaywrightBrowserDriver()

        assert driver._playwright is None
        assert driver._browser is None
        assert driver._browser_type == "chromium"

    def test_get_browser_type(self):
        """Test getting browser type"""
        driver = PlaywrightBrowserDriver()
        assert driver.get_browser_type() == "chromium"

    def test_set_browser_type_valid(self):
        """Test setting valid browser type"""
        driver = PlaywrightBrowserDriver()
        driver.set_browser_type("firefox")
        assert driver._browser_type == "firefox"

    def test_set_browser_type_invalid(self):
        """Test setting invalid browser type raises error"""
        driver = PlaywrightBrowserDriver()

        with pytest.raises(ValueError, match="Invalid browser type"):
            driver.set_browser_type("invalid")

    def test_is_running_when_not_started(self):
        """Test is_running returns False when browser not started"""
        driver = PlaywrightBrowserDriver()
        assert driver.is_running() is False

    @patch('nemesis.infrastructure.browser.playwright_adapter.sync_playwright')
    def test_launch_browser(self, mock_sync_playwright):
        """Test launching browser"""
        # Setup mocks
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_browser.is_connected.return_value = True

        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser

        # Launch browser
        driver = PlaywrightBrowserDriver()
        browser = driver.launch(headless=True)

        # Verify
        assert isinstance(browser, PlaywrightBrowserAdapter)
        assert driver.is_running() is True
        mock_playwright_instance.chromium.launch.assert_called_once_with(
            headless=True,
            args=[]
        )

    @patch('nemesis.infrastructure.browser.playwright_adapter.sync_playwright')
    def test_close_browser(self, mock_sync_playwright):
        """Test closing browser"""
        # Setup
        mock_playwright_instance = Mock()
        mock_browser = Mock()
        mock_browser.is_connected.return_value = True

        mock_sync_playwright.return_value.start.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser

        # Launch and close
        driver = PlaywrightBrowserDriver()
        driver.launch()
        driver.close()

        # Verify
        mock_browser.close.assert_called_once()
        mock_playwright_instance.stop.assert_called_once()
        assert driver._browser is None
        assert driver._playwright is None

    def test_save_trace_without_browser(self):
        """Test save_trace raises error when browser not running"""
        driver = PlaywrightBrowserDriver()

        with pytest.raises(RuntimeError, match="Browser not running"):
            driver.save_trace(Path("/tmp/trace.zip"))

    def test_save_video_without_browser(self):
        """Test save_video returns None when browser not running"""
        driver = PlaywrightBrowserDriver()
        result = driver.save_video(Path("/tmp/video.webm"))
        assert result is None

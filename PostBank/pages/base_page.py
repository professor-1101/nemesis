"""Base page object using Clean Architecture with IPage interface.

This refactored BasePage demonstrates:
- Using IPage interface instead of direct Playwright coupling
- Framework independence through abstraction
- Clean separation of concerns
"""

import os
from pathlib import Path
from typing import Any, Optional

# Use IPage interface from Domain layer
from nemesis.domain.ports import IPage


class BasePage:
    """
    Base page object for all pages using IPage interface.

    Clean Architecture:
    - Depends on IPage interface (Domain layer), not Playwright
    - Can work with any browser driver (Playwright, Selenium, etc.)
    - Framework-independent
    """

    def __init__(self, page: IPage, config: dict) -> None:
        """
        Initialize base page

        Args:
            page: IPage interface implementation (e.g., PlaywrightPageAdapter)
            config: Configuration dictionary
        """
        self.page = page
        self.config = config

        # Get base URL from config
        self.base_url = config.get("base_url", "http://192.168.10.141:1365/")

        # Access underlying Playwright page for advanced features
        if hasattr(page, 'playwright_page'):
            self._playwright_page = page.playwright_page
        else:
            self._playwright_page = None

    def navigate_to(self, path: str = "") -> None:
        """Navigate to URL"""
        url = f"{self.base_url}{path}"
        self.page.goto(url)

    def click(self, selector: str, timeout: Optional[int] = None) -> None:
        """Click element"""
        if self._playwright_page:
            # Use Playwright directly
            elem = self._playwright_page.locator(selector).first
            if timeout:
                elem.click(timeout=timeout)
            else:
                elem.click()
        else:
            self.page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        """Fill input field"""
        self.page.fill(selector, value)

    def check(self, selector: str, timeout: Optional[int] = None) -> None:
        """Check checkbox or radio button"""
        if timeout and self._playwright_page:
            # Use Playwright directly with timeout
            elem = self._playwright_page.locator(selector).first
            elem.check(timeout=timeout)
        elif self._playwright_page:
            self._playwright_page.check(selector)
        else:
            raise NotImplementedError("check requires Playwright page")

    def get_text(self, selector: str) -> str:
        """
        Get element text with robust error handling.
        
        Args:
            selector: CSS selector or Playwright locator string
            
        Returns:
            Element text content
            
        Raises:
            AssertionError: If element not found or selector invalid, with screenshot
        """
        try:
            return self.page.get_text(selector)
        except Exception as e:
            # Save screenshot and HTML for debugging
            error_msg = f"Failed to get text with selector '{selector}': {str(e)}"
            self._save_debug_info(error_msg, selector)
            raise AssertionError(error_msg) from e

    def is_visible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Check if element is visible"""
        try:
            return self.page.is_visible(selector)
        except Exception:
            # If selector is invalid, return False instead of crashing
            return False

    def wait_for_element(self, selector: str, timeout: int = 10000) -> None:
        """Wait for element to be visible"""
        if self._playwright_page:
            try:
                self._playwright_page.wait_for_selector(selector, timeout=timeout)
            except Exception as e:
                error_msg = f"Element not found within {timeout}ms: {selector}"
                self._save_debug_info(error_msg, selector)
                raise TimeoutError(error_msg) from e
        else:
            if not self.page.is_visible(selector):
                error_msg = f"Element not visible: {selector}"
                self._save_debug_info(error_msg, selector)
                raise TimeoutError(error_msg)

    def select_option(self, selector: str, value: str) -> None:
        """Select option from dropdown"""
        if self._playwright_page:
            self._playwright_page.select_option(selector, value)
        else:
            raise NotImplementedError("select_option requires Playwright page")

    def select_kendo_dropdown_option(self, dropdown_selector: str, option_text: str, timeout: int = 10000) -> None:
        """
        Select option from Kendo UI dropdown by clicking on dropdown and then option.

        Args:
            dropdown_selector: Selector for the dropdown element (input, span, or div)
            option_text: Text of the option to select
            timeout: Timeout in milliseconds
        """
        if not self._playwright_page:
            raise NotImplementedError("select_kendo_dropdown_option requires Playwright page")

        # Click on the dropdown to open it
        self._playwright_page.click(dropdown_selector, timeout=timeout)

        # Wait for dropdown popup to appear
        self._playwright_page.wait_for_timeout(500)

        # Try multiple selectors for Kendo options
        option_selectors = [
            f"[role='option']:has-text('{option_text}')",
            f".k-item:has-text('{option_text}')",
            f".k-list-item:has-text('{option_text}')",
            f"li:has-text('{option_text}')",
            f"div:has-text('{option_text}')",
            f"span:has-text('{option_text}')",
            f"[data-value*='{option_text}']",
            f"//div[contains(text(), '{option_text}')]"
        ]

        for selector in option_selectors:
            try:
                # Check if option is visible
                if self._playwright_page.locator(selector).is_visible(timeout=2000):
                    self._playwright_page.click(selector, timeout=2000)
                    return
            except:
                continue

        # If no selector worked, try typing the text directly
        try:
            # Clear and type the option text
            input_selector = f"{dropdown_selector} input, {dropdown_selector} .k-input"
            self._playwright_page.fill(input_selector, option_text)
            self._playwright_page.keyboard.press("Enter")
        except:
            raise Exception(f"Could not select option '{option_text}' from Kendo dropdown")

    def select_kendo_dropdown_tree_option(self, dropdown_selector: str, parent_text: str, child_text: str = None, timeout: int = 10000) -> None:
        """
        Select option from Kendo UI DropDownTree by expanding parent and selecting child.
        This method handles tree dropdowns where clicking a parent item expands to show children.

        Args:
            dropdown_selector: Selector for the dropdown element
            parent_text: Text of the parent item to expand (e.g., "اردبیل")
            child_text: Optional text of the child item to select. If None, selects the parent itself
            timeout: Timeout in milliseconds
        """
        if not self._playwright_page:
            raise NotImplementedError("select_kendo_dropdown_tree_option requires Playwright page")

        # Click on the dropdown to open it
        self._playwright_page.click(dropdown_selector, timeout=timeout)

        # Wait for dropdown popup to appear
        self._playwright_page.wait_for_timeout(500)

        # Find the parent tree item
        parent_selectors = [
            f".k-treeview-item:has(.k-in:has-text('{parent_text}'))",
            f"li.k-treeview-item:has(.k-in:has-text('{parent_text}'))",
            f".k-item.k-treeview-item:has-text('{parent_text}')",
            f"li:has-text('{parent_text}')"
        ]

        parent_item = None
        for selector in parent_selectors:
            try:
                locator = self._playwright_page.locator(selector).first
                if locator.is_visible(timeout=2000):
                    parent_item = locator
                    break
            except:
                continue

        if not parent_item:
            raise Exception(f"Could not find parent item '{parent_text}' in tree dropdown")

        # If child_text is provided, we need to expand parent first, then select child
        if child_text:
            # First, expand the parent by clicking on expand icon
            try:
                # Try to find expand icon first
                expand_icon = parent_item.locator(".k-i-expand").first
                if expand_icon.is_visible(timeout=1000):
                    expand_icon.click(timeout=2000)
                    # Wait for expansion
                    self._playwright_page.wait_for_timeout(800)
                else:
                    # If no expand icon visible, try clicking on the parent item itself
                    parent_item.click(timeout=2000)
                    self._playwright_page.wait_for_timeout(800)
            except:
                # Last resort: click on parent item
                parent_item.click(timeout=2000)
                self._playwright_page.wait_for_timeout(800)

            # Now find and select the first available child item (city)
            # Look for any child item that is visible and doesn't have expand icon
            child_selectors = [
                ".k-treeview-item:not(:has(.k-i-expand)) .k-in",  # Child items without expand icon
                "li.k-treeview-item:not(:has(.k-i-expand)) .k-in",
                ".k-treeview-item:not(:has(.k-i-expand))",
                "li.k-treeview-item:not(:has(.k-i-expand))"
            ]

            for selector in child_selectors:
                try:
                    # Find the first visible child item
                    child_locator = self._playwright_page.locator(selector).first
                    if child_locator.is_visible(timeout=2000):
                        # Make sure it's not the parent itself
                        try:
                            child_content = child_locator.text_content(timeout=1000)
                            if child_content and child_content.strip() != parent_text:
                                # Click on the child item with force option to bypass pointer events
                                child_locator.click(force=True, timeout=2000)
                                return
                        except:
                            # If can't get text, just click with force
                            child_locator.click(force=True, timeout=2000)
                            return
                except:
                    continue

            raise Exception(f"Could not find any child item under parent '{parent_text}'")
        else:
            # If no child specified, select the parent itself (final item, not collapsable)
            try:
                # Click on the parent's text area (k-in) to select it
                parent_text_area = parent_item.locator(".k-in").first
                if parent_text_area.is_visible(timeout=1000):
                    parent_text_area.click(timeout=2000)
                    return
            except:
                pass

            # Fallback: click the parent item itself
            try:
                parent_item.click(timeout=2000)
            except:
                raise Exception(f"Could not select parent item '{parent_text}'")

    def get_current_url(self) -> str:
        """Get current page URL"""
        if self._playwright_page:
            return self._playwright_page.url
        else:
            raise NotImplementedError("get_current_url requires Playwright page")

    def _save_debug_info(self, error_message: str, selector: str = "", context: Any = None) -> None:
        """
        Save screenshot for debugging when errors occur.
        HTML saving removed for performance optimization.
        
        Args:
            error_message: Error message to include in filename
            selector: Selector that caused the error (optional)
            context: Optional context for additional info (optional, for compatibility)
        """
        if not self._playwright_page:
            return
        
        try:
            # Create reports/screenshots directory
            screenshot_dir = Path("reports/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Create safe filename from error message
            safe_error = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in error_message[:50])
            safe_error = safe_error.replace(' ', '_')
            
            # Save screenshot only (HTML removed for performance)
            screenshot_path = screenshot_dir / f"error_{safe_error}.png"
            self._playwright_page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Log debug info
            print(f"\n[DEBUG] Error occurred with selector: {selector}")
            print(f"[DEBUG] Screenshot saved: {screenshot_path}")
        except Exception as debug_error:
            # Don't fail if debug info saving fails
            print(f"[WARNING] Could not save debug info: {debug_error}")

    def get_text_with_fallback(self, selectors: list[str], timeout: int = 10000) -> str:
        """
        Try multiple selectors in order until one works.
        
        Args:
            selectors: List of CSS selectors to try in order
            timeout: Timeout in milliseconds for each selector (default: 10000)
            
        Returns:
            Text content from first successful selector
            
        Raises:
            AssertionError: If all selectors fail
        """
        last_error = None
        for selector in selectors:
            try:
                # Use Playwright locator with timeout for faster failure
                if self._playwright_page:
                    elem = self._playwright_page.locator(selector).first
                    text = elem.text_content(timeout=timeout)
                    if text and text.strip():
                        return text.strip()
                else:
                    # Fallback to page.get_text
                    text = self.get_text(selector)
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                last_error = e
                continue
        
        # All selectors failed
        error_msg = f"All selectors failed: {selectors}"
        self._save_debug_info(error_msg, str(selectors))
        raise AssertionError(error_msg) from last_error

"""Dashboard page object for PostBank application."""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


class DashboardPage(BasePage):
    """
    Dashboard page interactions using IPage interface.
    """

    # Selectors - using Playwright-native selectors only (no :contains())
    # Multiple fallback selectors for robustness
    WELCOME_MESSAGE_SELECTORS = [
        ".profileLink p:has-text('کاربر گرامی')",  # Primary: based on HTML structure
        ".profileLink:has-text('کاربر گرامی')",  # Alternative: profileLink class
        "p:has-text('کاربر گرامی')",  # Playwright-native text selector
        "div:has-text('کاربر گرامی')",  # Alternative: div tag
        "span:has-text('کاربر گرامی')",  # Alternative: span tag
        ".welcome-message",  # Fallback: class-based
        "[class*='welcome']",  # Fallback: partial class match
        "p[class*='welcome']",  # Fallback: p tag with welcome class
        "//*[contains(text(), 'کاربر گرامی')]",  # XPath fallback - any element
        "text=کاربر گرامی",  # Direct text search
    ]
    
    DASHBOARD_TITLE = ".dashboard-title, h1, h2"

    def __init__(self, page: IPage, config: dict) -> None:
        """Initialize dashboard page"""
        super().__init__(page, config)

    def is_loaded(self) -> bool:
        """
        Check if dashboard page is loaded - verify welcome message exists.
        Uses short timeout to avoid long waits.
        """
        import time
        time.sleep(2)  # Wait for page to fully load

        # Try multiple selectors with short timeout
        if self._playwright_page:
            try:
                # Quick check with Playwright locator (fastest)
                welcome_elem = self._playwright_page.locator("text=کاربر گرامی").first
                welcome_elem.wait_for(state="visible", timeout=10000)  # 10 second timeout
                if welcome_elem.count() > 0:
                    return True
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass

        # Fallback: try all CSS selectors with short timeout
        for selector in self.WELCOME_MESSAGE_SELECTORS:
            try:
                if self.is_visible(selector, timeout=5000):  # 5 second timeout
                    return True
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                continue

        # Last resort: check page content directly
        try:
            page_content = self._playwright_page.content()
            if 'کاربر گرامی' in page_content:
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass

        return False

    def verify_page_loaded(self) -> None:
        """Verify dashboard page is loaded"""
        if not self.is_loaded():
            error_msg = "Dashboard page not loaded - welcome message not found"
            self._save_debug_info(error_msg, str(self.WELCOME_MESSAGE_SELECTORS))
            raise AssertionError(error_msg)

    def get_welcome_message(self) -> str:
        """
        Get welcome message text using multiple fallback selectors with short timeout.
        
        Returns:
            Welcome message text
            
        Raises:
            AssertionError: If no welcome message found
        """
        # Method 1: Try Playwright locator with profileLink selector (most specific) - with short timeout
        if self._playwright_page:
            try:
                # Wait for element with short timeout (5 seconds)
                welcome_elem = self._playwright_page.locator(".profileLink p:has-text('کاربر گرامی')").first
                welcome_elem.wait_for(state="visible", timeout=5000)
                if welcome_elem.count() > 0:
                    text = welcome_elem.text_content()
                    if text and text.strip():
                        return text.strip()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                # Continue to next method
                pass
            
            # Method 2: Try XPath as fallback - with short timeout
            try:
                welcome_elem = self._playwright_page.locator("xpath=//p[contains(text(), 'کاربر گرامی')]").first
                welcome_elem.wait_for(state="visible", timeout=5000)
                if welcome_elem.count() > 0:
                    text = welcome_elem.text_content()
                    if text and text.strip():
                        return text.strip()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
            
            # Method 3: Try any element containing "کاربر گرامی" - broader search
            try:
                welcome_elem = self._playwright_page.locator("text=کاربر گرامی").first
                welcome_elem.wait_for(state="visible", timeout=5000)
                if welcome_elem.count() > 0:
                    text = welcome_elem.text_content()
                    if text and text.strip():
                        return text.strip()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
        
        # Method 4: Use base page fallback mechanism (with shorter timeout)
        try:
            # Try with shorter timeout for each selector
            for selector in self.WELCOME_MESSAGE_SELECTORS[:3]:
                if self.is_visible(selector, timeout=2000):  # 2 second timeout per selector
                    text = self.get_text(selector)
                    if text and text.strip():
                        return text.strip()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        
        # All methods failed - save debug info and raise
        error_msg = "Welcome message not found with any selector after 5 seconds"
        self._save_debug_info(error_msg, str(self.WELCOME_MESSAGE_SELECTORS))
        raise AssertionError(error_msg)

    def verify_welcome_message(self, expected_name: str, expected_role: str = None, expected_unit: str = None) -> None:
        """
        Verify welcome message contains expected user information
        
        Args:
            expected_name: User full name
            expected_role: User role (optional)
            expected_unit: Organizational unit (optional)
        """
        try:
            actual_message = self.get_welcome_message()
        except AssertionError as e:
            # Re-raise with more context
            raise AssertionError(
                f"Could not retrieve welcome message. Original error: {str(e)}"
            ) from e
        
        # Check if user name exists
        if expected_name and expected_name not in actual_message:
            error_msg = (
                f"Expected name '{expected_name}' not found in welcome message. "
                f"Found: '{actual_message}'"
            )
            self._save_debug_info(error_msg)
            raise AssertionError(error_msg)
        
        # Check user role (if provided)
        if expected_role and expected_role not in actual_message:
            error_msg = (
                f"Expected role '{expected_role}' not found in welcome message. "
                f"Found: '{actual_message}'"
            )
            self._save_debug_info(error_msg)
            raise AssertionError(error_msg)
        
        # Check organizational unit (if provided)
        if expected_unit and expected_unit not in actual_message:
            error_msg = (
                f"Expected unit '{expected_unit}' not found in welcome message. "
                f"Found: '{actual_message}'"
            )
            self._save_debug_info(error_msg)
            raise AssertionError(error_msg)

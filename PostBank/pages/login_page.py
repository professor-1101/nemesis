"""Login page object for PostBank application."""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


class LoginPage(BasePage):
    """
    Login page interactions using IPage interface.
    """

    # Selectors - using Playwright-native selectors only (no :contains())
    # Removed :contains() selectors as they are not valid in Playwright
    USERNAME_INPUT_SELECTORS = [
        "input[placeholder*='نام کاربری']",
        "input[name*='username']",
        "input[name*='user']",
        "input[id*='username']",
        "input[id*='user']",
        "input[type='text']:first-of-type",
        "input[type='text']"
    ]
    
    PASSWORD_INPUT_SELECTORS = [
        "input[type='password'][placeholder*='رمز']",
        "input[type='password'][name*='password']",
        "input[type='password'][name*='pass']",
        "input[type='password'][id*='password']",
        "input[type='password'][id*='pass']",
        "input[type='password']"
    ]
    
    LOGIN_BUTTON_SELECTORS = [
        "button:has-text('ورود به سامانه')",  # Playwright-native text selector
        "button[type='submit']",
        "input[type='submit']",
        "button"
    ]
    
    # Error message selectors - exclude captcha errors
    # Captcha errors are in data-testid="KendoFormInput-captchaText" and should be ignored
    ERROR_MESSAGE_SELECTORS = [
        # Try to find error messages NOT related to captcha
        "[data-testid='KendoFormInput-username'] [role='alert']",
        "[data-testid='KendoFormInput-password'] [role='alert']",
        ".error-message",
        ".alert-danger",
        ".alert-error",
        ".invalid-feedback",
        ".help-block",
        ".text-danger",
        "[class*='error']",
        "[class*='invalid']"
    ]
    
    # Selectors for username/password specific errors (excluding captcha)
    USERNAME_PASSWORD_ERROR_SELECTORS = [
        "[data-testid='KendoFormInput-username'] [role='alert']",
        "[data-testid='KendoFormInput-password'] [role='alert']",
        "input[name='username'] ~ [role='alert']",
        "input[name='password'] ~ [role='alert']",
        "input[name='username'] + [role='alert']",
        "input[name='password'] + [role='alert']",
    ]

    def __init__(self, page: IPage, config: dict) -> None:
        """Initialize login page"""
        super().__init__(page, config)

    def open(self) -> None:
        """Open login page - in SPA only base_url is used"""
        self.navigate_to("/")

    def enter_username(self, username: str) -> None:
        """Enter username - find input with label 'نام کاربری' using multiple methods"""
        # Early exit if no Playwright page
        if not self._playwright_page:
            self._try_fallback_selectors_for_username(username)
            return

        # Method 1A: Find label with text and input after it
        if self._try_username_via_label_sibling(username):
            return

        # Method 1B: Find label with text and input in ancestor form
        if self._try_username_via_label_form(username):
            return

        # Method 2: Find input with placeholder or name attributes
        if self._try_username_via_attributes(username):
            return

        # Method 3: Use fallback selectors
        self._try_fallback_selectors_for_username(username)

    def _try_username_via_label_sibling(self, username: str) -> bool:
        """Try to find username input as sibling of label."""
        try:
            label = self._playwright_page.locator("label:has-text('نام کاربری')")
            if label.count() == 0:
                return False

            input_after = label.first.locator("xpath=following-sibling::input[1]")
            if input_after.count() > 0:
                input_after.fill(username)
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        return False

    def _try_username_via_label_form(self, username: str) -> bool:
        """Try to find username input in form ancestor."""
        try:
            label = self._playwright_page.locator("label:has-text('نام کاربری')")
            if label.count() == 0:
                return False

            form = label.first.locator("xpath=ancestor::form[1]//input[1]")
            if form.count() > 0:
                form.fill(username)
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        return False

    def _try_username_via_attributes(self, username: str) -> bool:
        """Try to find username input via placeholder/name/id attributes."""
        try:
            input_elem = self._playwright_page.locator(
                "input[placeholder*='نام کاربری'], "
                "input[name*='username'], "
                "input[name*='user'], "
                "input[id*='username'], "
                "input[id*='user']"
            ).first
            if input_elem.count() > 0:
                input_elem.fill(username)
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        return False

    def _try_fallback_selectors_for_username(self, username: str) -> None:
        """Try fallback selectors for username - raises if all fail."""
        for selector in self.USERNAME_INPUT_SELECTORS:
            try:
                self.fill(selector, username)
                return
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                continue

        # All methods failed
        error_msg = f"Could not find username input field"
        self._save_debug_info(error_msg, str(self.USERNAME_INPUT_SELECTORS))
        raise AssertionError(error_msg)

    def enter_password(self, password: str) -> None:
        """Enter password - find input with label 'رمز عبور' using multiple methods"""
        # Early exit if no Playwright page
        if not self._playwright_page:
            self._try_fallback_selectors_for_password(password)
            return

        # Method 1A: Find label with text and password input after it
        if self._try_password_via_label_sibling(password):
            return

        # Method 1B: Find label with text and password input in ancestor form
        if self._try_password_via_label_form(password):
            return

        # Method 2: Find password input via placeholder/name/id attributes
        if self._try_password_via_attributes(password):
            return

        # Method 3: Use fallback selectors
        self._try_fallback_selectors_for_password(password)

    def _try_password_via_label_sibling(self, password: str) -> bool:
        """Try to find password input as sibling of label."""
        try:
            label = self._playwright_page.locator("label:has-text('رمز عبور')")
            if label.count() == 0:
                return False

            input_after = label.first.locator("xpath=following-sibling::input[@type='password'][1]")
            if input_after.count() > 0:
                input_after.fill(password)
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        return False

    def _try_password_via_label_form(self, password: str) -> bool:
        """Try to find password input in form ancestor."""
        try:
            label = self._playwright_page.locator("label:has-text('رمز عبور')")
            if label.count() == 0:
                return False

            form = label.first.locator("xpath=ancestor::form[1]//input[@type='password'][1]")
            if form.count() > 0:
                form.fill(password)
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        return False

    def _try_password_via_attributes(self, password: str) -> bool:
        """Try to find password input via placeholder/name/id attributes."""
        try:
            input_elem = self._playwright_page.locator(
                "input[type='password'][placeholder*='رمز'], "
                "input[type='password'][name*='password'], "
                "input[type='password'][name*='pass'], "
                "input[type='password'][id*='password'], "
                "input[type='password'][id*='pass']"
            ).first
            if input_elem.count() > 0:
                input_elem.fill(password)
                return True
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        return False

    def _try_fallback_selectors_for_password(self, password: str) -> None:
        """Try fallback selectors for password - raises if all fail."""
        for selector in self.PASSWORD_INPUT_SELECTORS:
            try:
                self.fill(selector, password)
                return
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                continue

        # All methods failed
        error_msg = f"Could not find password input field"
        self._save_debug_info(error_msg, str(self.PASSWORD_INPUT_SELECTORS))
        raise AssertionError(error_msg)

    def click_login_button(self) -> None:
        """Click login button - button 'ورود به سامانه' using multiple methods"""
        if self._playwright_page:
            # Method 1: Find button with text 'ورود به سامانه'
            try:
                button = self._playwright_page.locator("button:has-text('ورود به سامانه')").first
                if button.count() > 0:
                    button.click()
                    return
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
            
            # Method 2: Submit button
            try:
                button = self._playwright_page.locator("button[type='submit'], input[type='submit']").first
                if button.count() > 0:
                    button.click()
                    return
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
        
        # Method 3: Use fallback selectors
        for selector in self.LOGIN_BUTTON_SELECTORS:
            try:
                self.click(selector)
                return
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                continue
        
        # All methods failed
        error_msg = f"Could not find login button"
        self._save_debug_info(error_msg, str(self.LOGIN_BUTTON_SELECTORS))
        raise AssertionError(error_msg)

    def login(self, username: str, password: str) -> None:
        """Perform complete login flow"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()

    def get_error_message(self) -> str:
        """
        Get error message text - excludes captcha errors.
        Only returns errors related to username/password fields.
        """
        # First try to get username/password specific errors (exclude captcha)
        if self._playwright_page:
            # Try username field error
            try:
                username_error = self._playwright_page.locator(
                    "[data-testid='KendoFormInput-username'] [role='alert']"
                ).first
                if username_error.count() > 0:
                    text = username_error.text_content()
                    if text and text.strip() and 'عبارت امنیتی' not in text:
                        return text.strip()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
            
            # Try password field error
            try:
                password_error = self._playwright_page.locator(
                    "[data-testid='KendoFormInput-password'] [role='alert']"
                ).first
                if password_error.count() > 0:
                    text = password_error.text_content()
                    if text and text.strip() and 'عبارت امنیتی' not in text:
                        return text.strip()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass

            # Try general error messages (but exclude captcha)
            try:
                # Get all alert elements
                all_alerts = self._playwright_page.locator("[role='alert']")
                for i in range(all_alerts.count()):
                    alert = all_alerts.nth(i)
                    text = alert.text_content()
                    if text and text.strip():
                        # Skip captcha errors
                        if 'عبارت امنیتی' in text or 'captcha' in text.lower():
                            continue
                        # Skip if it's inside captcha field
                        parent = alert.locator("xpath=ancestor::div[contains(@data-testid, 'captcha')]")
                        if parent.count() == 0:  # Not inside captcha field
                            return text.strip()
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
        
        # Fallback: try selectors but filter out captcha errors
        try:
            error_text = self.get_text_with_fallback(self.ERROR_MESSAGE_SELECTORS)
            # Filter out captcha-related errors
            if error_text and 'عبارت امنیتی' not in error_text and 'captcha' not in error_text.lower():
                return error_text
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        
        return ""

    def is_error_visible(self) -> bool:
        """
        Check if error message is visible - excludes captcha errors.
        Only checks for username/password errors.
        """
        if self._playwright_page:
            # Check username/password specific errors
            try:
                username_error = self._playwright_page.locator(
                    "[data-testid='KendoFormInput-username'] [role='alert']"
                ).first
                if username_error.count() > 0:
                    text = username_error.text_content()
                    if text and text.strip() and 'عبارت امنیتی' not in text:
                        return True
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass

            try:
                password_error = self._playwright_page.locator(
                    "[data-testid='KendoFormInput-password'] [role='alert']"
                ).first
                if password_error.count() > 0:
                    text = password_error.text_content()
                    if text and text.strip() and 'عبارت امنیتی' not in text:
                        return True
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass

        # Fallback: check other selectors but exclude captcha
        for selector in self.ERROR_MESSAGE_SELECTORS:
            if self.is_visible(selector):
                # Double check it's not a captcha error
                try:
                    text = self.get_text(selector)
                    if text and 'عبارت امنیتی' not in text and 'captcha' not in text.lower():
                        return True
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    pass
        return False

    def is_on_login_page(self) -> bool:
        """Verify user is on login page"""
        # Try multiple selectors
        for selector in self.LOGIN_BUTTON_SELECTORS:
            if self.is_visible(selector):
                return True
        return False

    def verify_page_loaded(self) -> None:
        """Verify login page is loaded"""
        if not self.is_on_login_page():
            error_msg = "Login page not loaded"
            self._save_debug_info(error_msg, str(self.LOGIN_BUTTON_SELECTORS))
            raise AssertionError(error_msg)

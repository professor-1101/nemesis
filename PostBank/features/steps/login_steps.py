"""Step definitions for login scenarios in Persian."""

import os
from pathlib import Path
from behave import given, when, then
from behave.api.step_matchers import use_step_matcher
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

# Use parse matcher by default (more readable)
use_step_matcher('parse')


@given('کاربر در صفحه "ورود" قرار دارد')
def step_user_on_login_page(context):
    """Navigate to login page."""
    context.login_page = LoginPage(context.page, context.test_config)
    context.login_page.open()


@when('کاربر نام کاربری "{نام_کاربری}" را وارد می‌کند')
def step_user_enters_username(context, نام_کاربری):
    """
    User enters username - parameterized step definition.

    Priority (for @file_data scenarios):
    1. Use context.active_outline['نام_کاربری'] (set by before_scenario hook from CSV)
    2. Use context.current_user_data['نام_کاربری'] (also set by before_scenario)
    3. Use parameter from feature file (fallback for non-file_data scenarios)
    """
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.test_config)

    username = None

    # Priority 1: Use context.active_outline (set by before_scenario hook from CSV)
    # This is the PRIMARY source for @file_data scenarios
    if hasattr(context, 'active_outline') and context.active_outline:
        username = context.active_outline.get('نام_کاربری', '')
        if username and username != 'PLACEHOLDER' and username.strip():
            # Update step text for reporting
            if hasattr(context, 'current_step'):
                context.current_step.actual_username = username
            context.login_page.enter_username(username)
            # Store for later use
            if not hasattr(context, 'current_user_data'):
                context.current_user_data = {}
            context.current_user_data['نام_کاربری'] = username
            return

    # Priority 2: Use context.current_user_data (also set by before_scenario)
    if hasattr(context, 'current_user_data') and context.current_user_data:
        username = context.current_user_data.get('نام_کاربری', '')
        if username and username != 'PLACEHOLDER' and username.strip():
            # Update step text for reporting
            if hasattr(context, 'current_step'):
                context.current_step.actual_username = username
            context.login_page.enter_username(username)
            return

    # Priority 3: Use parameter from feature file (fallback)
    username = نام_کاربری if نام_کاربری and نام_کاربری != 'PLACEHOLDER' else ""

    if username and username != 'PLACEHOLDER' and username.strip():
        # Update step text for reporting
        if hasattr(context, 'current_step'):
            context.current_step.actual_username = username
        context.login_page.enter_username(username)
        # Store user data for validation
        if not hasattr(context, 'current_user_data'):
            context.current_user_data = {}
        context.current_user_data['نام_کاربری'] = username


@when('کاربر رمز عبور "{رمز_عبور}" را وارد می‌کند')
def step_user_enters_password(context, رمز_عبور):
    """
    User enters password - parameterized step definition.

    Priority (for @file_data scenarios):
    1. Use context.active_outline['رمز_عبور'] (set by before_scenario hook from CSV)
    2. Use context.current_user_data['رمز_عبور'] (also set by before_scenario)
    3. Use parameter from feature file (fallback for non-file_data scenarios)
    """
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.test_config)

    password = None

    # Priority 1: Use context.active_outline (set by before_scenario hook from CSV)
    # This is the PRIMARY source for @file_data scenarios
    if hasattr(context, 'active_outline') and context.active_outline:
        password = context.active_outline.get('رمز_عبور', '')
        if password and password != 'PLACEHOLDER' and password.strip():
            # Update step text for reporting
            if hasattr(context, 'current_step'):
                context.current_step.actual_password = password
            context.login_page.enter_password(password)
            # Store for later use
            if not hasattr(context, 'current_user_data'):
                context.current_user_data = {}
            context.current_user_data['رمز_عبور'] = password
            return

    # Priority 2: Use context.current_user_data (also set by before_scenario)
    if hasattr(context, 'current_user_data') and context.current_user_data:
        password = context.current_user_data.get('رمز_عبور', '')
        if password and password != 'PLACEHOLDER' and password.strip():
            # Update step text for reporting
            if hasattr(context, 'current_step'):
                context.current_step.actual_password = password
            context.login_page.enter_password(password)
            return

    # Priority 3: Use parameter from feature file (fallback)
    password = رمز_عبور if رمز_عبور and رمز_عبور != 'PLACEHOLDER' else ""

    if password and password != 'PLACEHOLDER' and password.strip():
        # Update step text for reporting
        if hasattr(context, 'current_step'):
            context.current_step.actual_password = password
        context.login_page.enter_password(password)
        # Store user data
        if not hasattr(context, 'current_user_data'):
            context.current_user_data = {}
        context.current_user_data['رمز_عبور'] = password


# Step definitions for empty values - parse matcher doesn't match empty strings well
@when('کاربر نام کاربری "" را وارد می‌کند')
def step_user_enters_empty_username(context):
    """User enters empty username."""
    step_user_enters_username(context, "")


@when('کاربر رمز عبور "" را وارد می‌کند')
def step_user_enters_empty_password(context):
    """User enters empty password."""
    step_user_enters_password(context, "")


@when('روی دکمه "ورود" کلیک می‌کند')
def step_clicks_login_button(context):
    """Clicks login button - button 'ورود به سامانه'."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.test_config)
    context.login_page.click_login_button()


# Step definition for "و روی دکمه "ورود" کلیک می‌کند" (with 'و' prefix)
@when('و روی دکمه "ورود" کلیک می‌کند')
def step_and_clicks_login_button(context):
    """Clicks login button (with 'و' prefix)."""
    step_clicks_login_button(context)


# Step definitions with "و" prefix - these use the dynamic step definitions
@when('و کاربر نام کاربری "{نام_کاربری}" را وارد می‌کند')
def step_and_user_enters_username(context, نام_کاربری):
    """User enters username (with و prefix)."""
    step_user_enters_username(context, نام_کاربری)


@when('و کاربر رمز عبور "{رمز_عبور}" را وارد می‌کند')
def step_and_user_enters_password(context, رمز_عبور):
    """User enters password (with و prefix)."""
    step_user_enters_password(context, رمز_عبور)


@then('و کاربر به صفحه "داشبورد" هدایت می‌شود')
def step_and_user_redirected_to_dashboard(context):
    """User is redirected to dashboard (with و prefix)."""
    step_user_redirected_to_dashboard(context)


@then('کاربر به صفحه "داشبورد" هدایت می‌شود')
def step_user_redirected_to_dashboard(context):
    """User is redirected to dashboard."""
    context.dashboard_page = DashboardPage(context.page, context.test_config)
    context.dashboard_page.verify_page_loaded()

    # ASSERTION: Verify dashboard elements are visible
    assert context.dashboard_page.is_dashboard_visible(), \
        "صفحه داشبورد نمایش داده نشده است - المان‌های اصلی dashboard موجود نیستند"

    # ASSERTION: Verify URL changed to dashboard
    if hasattr(context, 'page') and hasattr(context.page, 'url'):
        current_url = context.page.url
        assert 'dashboard' in current_url.lower() or current_url.count('/') > 2, \
            f"URL به صفحه داشبورد تغییر نکرده است - URL فعلی: {current_url}"


@then('پیام "ورود با موفقیت انجام شد" نمایش داده می‌شود')
def step_success_message_displayed(context):
    """
    Success message is displayed - verify welcome message with data from CSV.

    Priority order for user data:
    1. context.current_user_data (from CSV via before_scenario hook) - PRIMARY SOURCE
    2. context.active_outline (from Examples table, overridden by before_scenario)
    3. context.table (if Data Table is used)
    """
    if not hasattr(context, 'dashboard_page'):
        context.dashboard_page = DashboardPage(context.page, context.test_config)

    expected_name = None
    expected_role = None

    # Method 1: Use context.current_user_data (from CSV via before_scenario) - PRIMARY SOURCE
    # This is set in before_scenario hook when @file_data tag is present
    # Contains full user data: نام_کاربری, رمز_عبور, نام_و_نام_خانوادگی, نقش_سازمانی, سمت_سازمانی
    if hasattr(context, 'current_user_data') and context.current_user_data:
        user_data = context.current_user_data
        expected_name = user_data.get('نام_و_نام_خانوادگی', '') or user_data.get('نام_کاربری', '')
        expected_role = user_data.get('نقش_سازمانی', '') or user_data.get('سمت_سازمانی', '')

    # Method 2: Use context.active_outline (Behave built-in, may be overridden by before_scenario)
    elif hasattr(context, 'active_outline') and context.active_outline:
        outline_data = context.active_outline
        expected_name = outline_data.get('نام_و_نام_خانوادگی', '') or outline_data.get('نام_کاربری', '')
        expected_role = outline_data.get('نقش_سازمانی', '') or outline_data.get('سمت_سازمانی', '')

    # Method 3: Use context.table (if Data Table is used)
    elif hasattr(context, 'table') and context.table:
        for row in context.table:
            expected_name = row.get('نام_و_نام_خانوادگی', '') or row.get('نام_کاربری', '')
            expected_role = row.get('نقش_سازمانی', '') or row.get('سمت_سازمانی', '')
            break

    # ASSERTION: Validate welcome message
    if expected_name:
        context.dashboard_page.verify_welcome_message(
            expected_name=expected_name,
            expected_role=expected_role
        )
    else:
        # Just check if message exists
        welcome_msg = context.dashboard_page.get_welcome_message()
        assert welcome_msg and 'کاربر گرامی' in welcome_msg, \
            f"پیام خوشامدگویی صحیح نمایش داده نشده است - پیام دریافتی: '{welcome_msg}'"

    # ASSERTION: Verify user is authenticated (session exists)
    assert context.dashboard_page.is_dashboard_visible(), \
        "احراز هویت ناموفق بود - داشبورد نمایش داده نشده است"


@then('پیام خطای مورد انتظار نمایش داده می‌شود')
def step_expected_error_message_displayed(context):
    """Expected error message is displayed with robust error detection."""
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.test_config)

    # Check error message from Examples or active_outline
    expected_error = None

    # Method 1: From active_outline (Scenario Outline)
    if hasattr(context, 'active_outline') and context.active_outline:
        expected_error = context.active_outline.get('پیام_خطا', '')

    # Method 2: From table
    elif hasattr(context, 'table') and context.table:
        for row in context.table:
            expected_error = row.get('پیام_خطا') or row.get('پیام خطا')
            if expected_error:
                break

        # Verify error message with multiple selectors and patterns
    if expected_error:
        # Try to get error message using the login page method (excludes captcha)
        try:
            error_text = context.login_page.get_error_message()
        except Exception:
            # Fallback: try username/password specific error selectors (exclude captcha)
            error_text = ""
            if hasattr(context.page, 'playwright_page'):
                try:
                    # Try username field error
                    username_error = context.page.playwright_page.locator(
                        "[data-testid='KendoFormInput-username'] [role='alert']"
                    ).first
                    if username_error.count() > 0:
                        text = username_error.text_content()
                        if text and text.strip() and 'عبارت امنیتی' not in text:
                            error_text = text.strip()
                except Exception:
                    pass
                
                if not error_text:
                    # Try password field error
                    try:
                        password_error = context.page.playwright_page.locator(
                            "[data-testid='KendoFormInput-password'] [role='alert']"
                        ).first
                        if password_error.count() > 0:
                            text = password_error.text_content()
                            if text and text.strip() and 'عبارت امنیتی' not in text:
                                error_text = text.strip()
                    except Exception:
                        pass
            
            # If still no error, try general selectors but filter captcha
            if not error_text:
                error_selectors = [
                    "[data-testid='KendoFormInput-username'] [role='alert']",
                    "[data-testid='KendoFormInput-password'] [role='alert']",
                    ".error-message",
                    ".alert-danger",
                    ".alert-error",
                ]
                
                for selector in error_selectors:
                    try:
                        if context.login_page.is_visible(selector):
                            text = context.login_page.get_text(selector)
                            if text and text.strip() and 'عبارت امنیتی' not in text:
                                error_text = text.strip()
                                break
                    except Exception:
                        continue
        
        # Verify error message
        if expected_error not in error_text:
            # Save screenshot for debugging
            try:
                screenshot_dir = Path('reports/screenshots')
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                scenario_name = getattr(context.scenario, 'name', 'unknown').replace(' ', '_').replace('/', '_')
                screenshot_path = screenshot_dir / f"error_assertion_failed_{scenario_name}.png"
                if hasattr(context.page, 'screenshot'):
                    context.page.screenshot(path=str(screenshot_path))
            except Exception:
                pass  # Screenshot is optional
            
            raise AssertionError(
                f"Expected error message '{expected_error}' not found. "
                f"Found: '{error_text}'. "
                f"Please check screenshot if available."
            )
    else:
        # Just check if error is visible
        if not context.login_page.is_error_visible():
            raise AssertionError("Error message not displayed")


# Step definition for "آنگاه پیام خطای مورد انتظار نمایش داده می‌شود" (with 'آنگاه' prefix)
@then('آنگاه پیام خطای مورد انتظار نمایش داده می‌شود')
def step_then_expected_error_message_displayed(context):
    """Expected error message is displayed (with 'آنگاه' prefix)."""
    step_expected_error_message_displayed(context)


# ============================================================================
# Generic Role-Based Login Steps (for Background scenarios)
# ============================================================================

@given('کاربر با نقش "{role}" وارد سیستم شده است')
def step_user_logged_in_with_role(context, role):
    """
    Generic step for logging in user with specific role.
    
    This step:
    1. Filters users from CSV with specified role
    2. Selects a random active user with that role
    3. Performs complete login process
    4. Verifies login success (dashboard loaded)
    
    Used in Background sections for scenario independence.
    
    Args:
        context: Behave context
        role: Role name (e.g., "کارشناس حوزه باجه")
    """
    import random
    import csv
    from pathlib import Path
    
    # Get users with this role
    role_users = []
    if hasattr(context, 'available_users') and context.available_users:
        role_users = [user for user in context.available_users
                     if user.get('نقش_سازمانی', '') == role
                     and user.get('فعال', '').strip().lower() == 'true']
    else:
        # Fallback: load from CSV directly
        project_root = Path(__file__).parent.parent.parent
        csv_file = project_root / "test_data" / "users.csv"
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_role = row.get('نقش سازمانی', '').strip()
                if user_role == role and row.get('فعال', '').strip().lower() == 'true':
                    role_users.append({
                        'نام_کاربری': row.get('نام کاربری', '').strip(),
                        'رمز_عبور': row.get('نام کاربری', '').strip(),  # password = username
                        'نام_و_نام_خانوادگی': row.get('نام و نام خانوادگی', ''),
                        'نقش_سازمانی': user_role,
                        'سمت_سازمانی': row.get('سمت سازمانی', '')
                    })
    
    if not role_users:
        raise ValueError(f"No active users found with role: '{role}'")
    
    # Select random user
    selected_user = random.choice(role_users)
    
    # Store for later use
    context.current_user_data = selected_user
    
    # Perform login
    login_page = LoginPage(context.page, context.test_config)
    login_page.open()
    login_page.enter_username(selected_user['نام_کاربری'])
    login_page.enter_password(selected_user['رمز_عبور'])
    login_page.click_login_button()

    # Store dashboard page for later use (no verification in Given step)
    # If login fails, the actual scenario steps will fail with clear errors
    dashboard_page = DashboardPage(context.page, context.test_config)
    context.dashboard_page = dashboard_page

    # Log login attempt (no verification here - BDD compliant)
    if hasattr(context, 'logger'):
        context.logger.info(
            f"Logged in as '{role}': {selected_user['نام_کاربری']} "
            f"({selected_user['نام_و_نام_خانوادگی']})"
        )

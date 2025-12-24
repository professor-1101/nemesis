"""
Step definitions for applicant registration scenarios in Persian.

Clean implementation:
- Simplified user selection logic
- No code duplication
- Clear separation of concerns
"""

import random
from behave import given, when, then
from behave.api.step_matchers import use_step_matcher
from pages.applicant_registration_page import ApplicantRegistrationPage
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

# Use parse matcher by default (more readable)
use_step_matcher('parse')


def _select_random_user_by_role(context, role: str) -> dict:
    """
    Select a random active user with specified role from CSV.

    Helper function to reduce code duplication.

    Args:
        context: Behave context
        role: Persian role name (e.g., "کارشناس حوزه باجه")

    Returns:
        dict: Selected user data

    Raises:
        ValueError: If no active users found with specified role
    """
    import csv
    from pathlib import Path

    # Check if users already loaded in context
    if hasattr(context, 'available_users') and context.available_users:
        role_users = [
            user for user in context.available_users
            if user.get('نقش_سازمانی', '') == role
            and user.get('فعال', '').strip().lower() == 'true'
        ]
        if role_users:
            return random.choice(role_users)

    # Load from CSV if not in context
    project_root = Path(__file__).parent.parent.parent
    csv_file = project_root / "test_data" / "users.csv"

    role_users = []
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

    return random.choice(role_users)


@given('کاربر در نقش کارشناس حوزه باجه ها قرار دارد')
def step_user_is_baje_expert(context):
    """
    Login as a random "کارشناس حوزه باجه" user from CSV.

    Clean implementation using helper function.
    """
    # Select random user with helper function
    selected_user = _select_random_user_by_role(context, 'کارشناس حوزه باجه')

    # Store for later use
    context.current_user_data = selected_user

    # Perform login
    login_page = LoginPage(context.page, context.test_config)
    login_page.open()
    login_page.enter_username(selected_user['نام_کاربری'])
    login_page.enter_password(selected_user['رمز_عبور'])
    login_page.click_login_button()

    # Verify login success
    dashboard_page = DashboardPage(context.page, context.test_config)
    dashboard_page.verify_page_loaded()

    # Log successful login
    context.logger.info(
        f"Successfully logged in as baje expert: {selected_user['نام_کاربری']} "
        f"({selected_user['نقش_سازمانی']})"
    )


@given('کاربر در صفحه ثبت متقاضی قرار دارد')
def step_user_on_applicant_registration_page_simple(context):
    """Navigate to applicant registration page"""
    context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)
    context.applicant_page.navigate_to_applicant_registration()


@when('کاربر دکمه "اضافه کردن" را کلیک می‌کند')
def step_user_clicks_add_button(context):
    """Click the add button to create new applicant"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    context.applicant_page.click_add_button()


@when('کاربر دکمه دوم "اضافه کردن" را کلیک می‌کند')
def step_user_clicks_second_add_button(context):
    """Click the second add button on the applicant page"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    context.applicant_page.click_second_add_button()


@then('به صفحه "متقاضی" منتقل می‌شود')
def step_user_navigated_to_applicant_page(context):
    """Verify user is navigated to applicant page with breadcrumb"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    if not context.applicant_page.verify_applicant_breadcrumb_visible():
        raise AssertionError("Applicant breadcrumb not visible - not navigated to applicant page")


# Removed duplicate step definitions:
# - و کاربر دکمه دوم "اضافه کردن" را کلیک می‌کند
# - then کاربر دکمه دوم "اضافه کردن" را کلیک می‌کند
# These are redundant with the @when definition above


@then('به صفحه "اطلاعات شخص" منتقل می‌شود')
def step_user_navigated_to_personal_info_page(context):
    """Verify user is navigated to personal information page"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    if not context.applicant_page.verify_personal_info_breadcrumb_visible():
        raise AssertionError("Personal info breadcrumb not visible - not navigated to personal info page")


@when('کاربر فیلد های الزامی را تکمیل می کند')
def step_user_fills_required_fields(context):
    """
    Fill required fields with random Persian test data.

    Simplified implementation:
    - PersianDataGenerator handles data generation
    - No complex override mapping needed
    """
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    # Override with test data from Examples table if provided (simple pass-through)
    overrides = {}
    if hasattr(context, 'table') and context.table:
        for row in context.table:
            if 'نام' in row:
                overrides['name'] = row['نام']
            if 'نام خانوادگی' in row:
                overrides['family_name'] = row['نام خانوادگی']
            break

    # Fill form (data generation handled by PersianDataGenerator)
    context.applicant_page.fill_personal_info_form(**overrides)


# Removed duplicate step:
# @then('کاربر فیلد های الزامی را تکمیل می کند')
# This is redundant with the @when definition above


@when('کاربر دکمه "ذخیره" را کلیک می‌کند')
def step_user_clicks_save_button(context):
    """Click the save button"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    context.applicant_page.click_save_button()


@then('اطلاعات متقاضی به کارشناس اداره کل جهت تعیین تکلیف نتیجه آزمون ارسال میشود')
def step_applicant_info_sent_to_admin_expert(context):
    """Verify applicant information is sent to admin expert"""
    # This would typically check for success message or verify data was saved
    # For now, we'll check for success message
    if hasattr(context, 'applicant_page'):
        if context.applicant_page.is_success_message_displayed():
            context.logger.info("Applicant information successfully sent to admin expert")
        else:
            raise AssertionError("Success message not displayed after saving applicant")

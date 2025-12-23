"""Step definitions for applicant registration scenarios in Persian."""

import random
from behave import given, when, then
from behave.api.step_matchers import use_step_matcher
from pages.applicant_registration_page import ApplicantRegistrationPage
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

# Use parse matcher by default (more readable)
use_step_matcher('parse')


@given('کاربر در نقش کارشناس حوزه باجه ها قرار دارد')
def step_user_is_baje_expert(context):
    """
    Login as a random "کارشناس حوزه باجه" user from CSV.
    This step handles the complete login process for baje experts.
    """
    # Filter users with "کارشناس حوزه باجه" role
    baje_experts = []
    if hasattr(context, 'available_users') and context.available_users:
        baje_experts = [user for user in context.available_users
                       if user.get('نقش_سازمانی', '') == 'کارشناس حوزه باجه' and user.get('فعال', '').strip().lower() == 'true']

    if not baje_experts:
        # Fallback: load from CSV directly
        import csv
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        csv_file = project_root / "test_data" / "users.csv"

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                role = row.get('نقش سازمانی', '').strip()
                if role == 'کارشناس حوزه باجه' and row.get('فعال', '').strip().lower() == 'true':
                    baje_experts.append({
                        'نام_کاربری': row.get('نام کاربری', '').strip(),
                        'رمز_عبور': row.get('نام کاربری', '').strip(),  # password = username
                        'نام_و_نام_خانوادگی': row.get('نام و نام خانوادگی', ''),
                        'نقش_سازمانی': role,
                        'سمت_سازمانی': row.get('سمت سازمانی', '')
                    })

    if not baje_experts:
        raise ValueError("No active 'کارشناس حوزه باجه' users found in CSV")

    # Select random user
    selected_user = random.choice(baje_experts)

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


@when('و کاربر دکمه دوم "اضافه کردن" را کلیک می‌کند')
def step_and_user_clicks_second_add_button(context):
    """Click the second add button (with و prefix)"""
    step_user_clicks_second_add_button(context)


@then('کاربر دکمه دوم "اضافه کردن" را کلیک می‌کند')
def step_then_user_clicks_second_add_button(context):
    """Click the second add button (as then step - fallback)"""
    step_user_clicks_second_add_button(context)


@then('به صفحه "اطلاعات شخص" منتقل می‌شود')
def step_user_navigated_to_personal_info_page(context):
    """Verify user is navigated to personal information page"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    if not context.applicant_page.verify_personal_info_breadcrumb_visible():
        raise AssertionError("Personal info breadcrumb not visible - not navigated to personal info page")


@when('کاربر فیلد های الزامی را تکمیل می کند')
def step_user_fills_required_fields(context):
    """Fill required fields with random Persian test data"""
    if not hasattr(context, 'applicant_page'):
        context.applicant_page = ApplicantRegistrationPage(context.page, context.test_config)

    # Override with test data from Examples table if provided
    overrides = {}
    if hasattr(context, 'table') and context.table:
        for row in context.table:
            # Map Persian column names to English field names
            if 'نام' in row:
                overrides['name'] = row['نام']
            if 'نام خانوادگی' in row:
                overrides['family_name'] = row['نام خانوادگی']
            break

    # Fill form with random data (overridden by Examples data if provided)
    context.applicant_page.fill_personal_info_form(**overrides)


@then('کاربر فیلد های الزامی را تکمیل می کند')
def step_then_user_fills_required_fields(context):
    """Fill required fields (as then step - fallback)"""
    step_user_fills_required_fields(context)


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

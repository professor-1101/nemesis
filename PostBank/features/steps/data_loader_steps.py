"""Step definitions for loading test data from external files."""

import csv
import json
import os
from pathlib import Path
from behave import when, then
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


def get_test_data_path(filename: str) -> Path:
    """Get absolute path to test data file."""
    # PostBank project path
    project_root = Path(__file__).parent.parent.parent
    test_data_dir = project_root / "test_data"
    file_path = test_data_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")
    
    return file_path


def load_users_from_csv(filepath: Path) -> list:
    """Load users from CSV file."""
    users = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users


def load_users_from_json(filepath: Path) -> list:
    """Load users from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


@when('کاربران از فایل "{filename}" خوانده می‌شوند')
def step_load_users_from_file(context, filename):
    """Load users from external file (CSV or JSON)."""
    filepath = get_test_data_path(filename)
    
    if filename.endswith('.csv'):
        context.users_data = load_users_from_csv(filepath)
    elif filename.endswith('.json'):
        context.users_data = load_users_from_json(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filename}. Use .csv or .json")
    
    context.logger.info(f"Loaded {len(context.users_data)} users from {filename}")


@when('برای هر کاربر لاگین انجام می‌شود')
def step_login_for_each_user(context):
    """Login for each user loaded from file."""
    if not hasattr(context, 'users_data'):
        raise ValueError("No users data loaded. Use 'کاربران از فایل خوانده می‌شوند' step first.")
    
    context.login_results = []
    
    for user in context.users_data:
        # Use actual CSV file headers
        username = user.get('نام کاربری') or user.get('username')
        # password is the same as username
        password = username
        role = user.get('نقش سازمانی') or user.get('سمت سازمانی') or user.get('role', 'نامشخص')
        full_name = user.get('نام و نام خانوادگی', '')
        is_active = user.get('فعال', 'False')
        
        if not username:
            context.logger.warning(f"Skipping user with missing credentials: {user}")
            continue
        
        try:
            # Open login page for each user
            login_page = LoginPage(context.page, context.test_config)
            login_page.open()
            
            # Perform login
            login_page.enter_username(username)
            login_page.enter_password(password)
            login_page.click_login_button()
            
            # Check login success
            dashboard_page = DashboardPage(context.page, context.test_config)
            is_success = dashboard_page.is_loaded()
            
            result = {
                'username': username,
                'role': role,
                'success': is_success,
                'error': None
            }
            
            context.login_results.append(result)
            context.logger.info(f"Login {'successful' if is_success else 'failed'} for user: {username} ({role})")
            
        except Exception as e:
            result = {
                'username': username,
                'role': role,
                'success': False,
                'error': str(e)
            }
            context.login_results.append(result)
            context.logger.error(f"Login failed for user {username}: {e}")


@then('همه کاربران با موفقیت وارد می‌شوند')
def step_all_users_login_successfully(context):
    """Verify all users logged in successfully."""
    if not hasattr(context, 'login_results'):
        raise ValueError("No login results found. Run login step first.")
    
    failed_logins = [r for r in context.login_results if not r['success']]
    
    if failed_logins:
        error_messages = []
        for result in failed_logins:
            error_msg = f"User {result['username']} ({result['role']}) failed"
            if result['error']:
                error_msg += f": {result['error']}"
            error_messages.append(error_msg)
        
        raise AssertionError(
            f"{len(failed_logins)} out of {len(context.login_results)} users failed to login:\n"
            + "\n".join(error_messages)
        )
    
    context.logger.info(f"All {len(context.login_results)} users logged in successfully")


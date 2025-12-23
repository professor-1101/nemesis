"""Behave environment file for PostBank automation.

This file delegates to Nemesis framework hooks for proper lifecycle management.
Following Clean Architecture principles, test projects should use framework hooks
rather than implementing their own lifecycle management.
"""

import csv
import sys
import os
import random
from pathlib import Path
from typing import Any

# Fix encoding for Windows to handle Persian characters
if sys.platform == 'win32':
    import io
    # Set UTF-8 encoding for stdout/stderr
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # Set environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import framework hooks - these handle all lifecycle management
from nemesis.infrastructure.environment.hooks import (
    before_all as framework_before_all,
    after_all as framework_after_all,
    before_feature as framework_before_feature,
    after_feature as framework_after_feature,
    before_scenario as framework_before_scenario,
    after_scenario as framework_after_scenario,
    before_step as framework_before_step,
    after_step as framework_after_step
)


def load_users_from_csv() -> list:
    """Load users from CSV file for data-driven testing."""
    project_root = Path(__file__).parent.parent
    csv_file = project_root / "test_data" / "users.csv"

    if not csv_file.exists():
        return []

    users = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('نام کاربری', '').strip()
            if username:
                users.append({
                    'نام_کاربری': username,
                    'رمز_عبور': username,  # password is the same as username
                    'نام_و_نام_خانوادگی': row.get('نام و نام خانوادگی', ''),
                    'نقش_سازمانی': row.get('نق سازمانی', ''),
                    'سمت_سازمانی': row.get('سمت سازمانی', ''),
                    'نقش': row.get('نقش سازمانی', '') or row.get('سمت سازمانی', 'نامشخص'),
                    'فعال': row.get('فعال', 'True').strip()  # Include active status
                })
    return users


def before_feature(context: Any, feature: Any) -> None:
    """
    Before each feature - extend framework hook to inject CSV data.
    
    This hook:
    1. Loads users from CSV file
    2. Filters active users (فعال = True)
    3. Stores them in context for random selection in before_scenario
    4. For scenarios with @file_data tag, replaces Examples table with CSV users
    """
    # Call framework hook first
    framework_before_feature(context, feature)
    
    # Check if any scenario has @file_data tag
    has_file_data_tag = False
    if hasattr(feature, 'scenarios'):
        for scenario in feature.scenarios:
            if hasattr(scenario, 'tags'):
                # Handle both string tags and Tag objects
                tag_names = []
                for tag in scenario.tags:
                    if isinstance(tag, str):
                        tag_names.append(tag)
                    elif hasattr(tag, 'name'):
                        tag_names.append(tag.name)
                    elif hasattr(tag, 'value'):
                        tag_names.append(tag.value)
                    else:
                        tag_names.append(str(tag))
                if 'file_data' in tag_names:
                    has_file_data_tag = True
                    break
    
    # If feature has file_data tag, load users from CSV and replace Examples table
    if has_file_data_tag:
        users = load_users_from_csv()
        
        # Filter only active users (فعال = True)
        active_users = [user for user in users if user.get('فعال', '').strip().lower() in ('true', '1', 'yes', 'y', 'فعال')]
        if not active_users:
            active_users = users  # Fallback to all users if no active filter
        
        # Store active users in context for use in before_scenario
        context.available_users = active_users
        
        # Replace Examples table with CSV users for Scenario Outlines
        # This allows Behave to create scenarios for each user, but we'll override in before_scenario
        for scenario in feature.scenarios:
            if hasattr(scenario, 'examples') and scenario.examples:
                for example in scenario.examples:
                    # Check if this is the examples table we want to populate (with 'کاربران' in name)
                    if hasattr(example, 'name') and 'کاربران' in example.name:
                        # Replace Examples table rows with CSV users
                        # But keep only one placeholder row - we'll use random selection in before_scenario
                        # This way, only one scenario is created, and we inject random user each time
                        if hasattr(example, 'table') and example.table:
                            # Clear existing rows (keep header)
                            # We'll use the placeholder row and override in before_scenario
                            # Mark for dynamic population
                            example._needs_dynamic_data = True
                            example._csv_users = active_users


def before_scenario(context: Any, scenario: Any) -> None:
    """
    Before each scenario - extend to store user data from Examples and load random user from CSV.

    For scenarios with @file_data tag:
    - Randomly selects ONE user from CSV active users
    - Overrides active_outline with selected user data
    - Stores user data in context for step definitions

    This ensures each scenario execution uses a different random user from CSV.
    """
    try:
        # Call framework hook
        framework_before_scenario(context, scenario)
    except KeyError as e:
        print(f"[DEBUG] KeyError in framework_before_scenario: {e}")
        # Continue anyway
        pass
    
    # Check if scenario has @file_data tag and if we have available users
    has_file_data_tag = False
    if hasattr(scenario, 'tags'):
        tag_names = []
        for tag in scenario.tags:
            if isinstance(tag, str):
                tag_names.append(tag)
            elif hasattr(tag, 'name'):
                tag_names.append(tag.name)
            elif hasattr(tag, 'value'):
                tag_names.append(tag.value)
            else:
                tag_names.append(str(tag))
        if 'file_data' in tag_names:
            has_file_data_tag = True
    
    # If scenario needs random user and we have available users, select one randomly
    if has_file_data_tag and hasattr(context, 'available_users') and context.available_users:
        # Randomly select one user for THIS scenario execution
        # This ensures each scenario run uses a different random user
        selected_user = random.choice(context.available_users)
        
        # Log selected user for debugging
        if hasattr(context, 'logger'):
            context.logger.info(
                f"Selected random user from CSV: {selected_user.get('نام_کاربری', 'N/A')} "
                f"({selected_user.get('نام_و_نام_خانوادگی', 'N/A')})"
            )
        else:
            print(f"[DEBUG] Selected random user from CSV: {selected_user.get('نام_کاربری', 'N/A')} "
                  f"({selected_user.get('نام_و_نام_خانوادگی', 'N/A')})")
        
        # Create user data dictionary
        user_data = {
            'نام_کاربری': selected_user.get('نام_کاربری', ''),
            'رمز_عبور': selected_user.get('رمز_عبور', ''),  # Password = username from CSV
            'نام_و_نام_خانوادگی': selected_user.get('نام_و_نام_خانوادگی', ''),
            'نقش_سازمانی': selected_user.get('نقش_سازمانی', ''),
            'سمت_سازمانی': selected_user.get('سمت_سازمانی', '')
        }
        
        # Store in context.active_outline for step definitions to access
        # This is critical - step definitions check context.active_outline first
        if hasattr(context, 'active_outline') and context.active_outline:
            # If it's a Row object (from behave), update it
            if hasattr(context.active_outline, 'update'):
                context.active_outline.update(user_data)
            else:
                # If it's a Row object, set attributes directly
                for key, value in user_data.items():
                    setattr(context.active_outline, key, value)
        else:
            context.active_outline = user_data.copy()
        
        # If this is a Scenario Outline, also inject into scenario.active_outline
        # This overrides the placeholder values from Examples table
        if hasattr(scenario, 'active_outline') and scenario.active_outline is not None:
            # Update active_outline with random user data from CSV
            scenario.active_outline.update(user_data)
        else:
            # Initialize active_outline if it doesn't exist
            scenario.active_outline = user_data.copy()
        
        # Store in context.current_user_data for use in step definitions
        # This is the primary source of truth for user data in steps
        context.current_user_data = user_data
        
        # Debug: Print to verify data is set
        print(f"[DEBUG] context.active_outline set: {context.active_outline.get('نام_کاربری', 'NOT SET')}")
        print(f"[DEBUG] context.current_user_data set: {context.current_user_data.get('نام_کاربری', 'NOT SET')}")
    
    # If Scenario Outline (and not already handled above), add user data from Examples to context
    # This handles scenarios without @file_data tag (uses Examples table as-is)
    elif hasattr(scenario, 'active_outline') and scenario.active_outline:
        # Store user data for use in step definitions
        context.current_user_data = dict(scenario.active_outline)


# Delegate other hooks to framework
def before_all(context: Any) -> None:
    """Before all tests."""
    framework_before_all(context)


def after_all(context: Any) -> None:
    """After all tests."""
    framework_after_all(context)


def after_feature(context: Any, feature: Any) -> None:
    """After each feature."""
    framework_after_feature(context, feature)


def after_scenario(context: Any, scenario: Any) -> None:
    """After each scenario."""
    framework_after_scenario(context, scenario)


def before_step(context: Any, step: Any) -> None:
    """Before each step."""
    # Update step name with actual data for better reporting
    if hasattr(context, 'current_user_data') and context.current_user_data:
        user_data = context.current_user_data
        username = user_data.get('نام_کاربری', '')
        password = user_data.get('رمز_عبور', '')

        if username and '"PLACEHOLDER"' in step.name:
            step.name = step.name.replace('"PLACEHOLDER"', f'"{username}"')
        if password and '"PLACEHOLDER"' in step.name:
            step.name = step.name.replace('"PLACEHOLDER"', f'"{password}"')

    framework_before_step(context, step)


def after_step(context: Any, step: Any) -> None:
    """After each step."""
    framework_after_step(context, step)


__all__ = [
    "before_all",
    "after_all",
    "before_feature",
    "after_feature",
    "before_scenario",
    "after_scenario",
    "before_step",
    "after_step",
]


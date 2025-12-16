"""Simplified login step definitions using Nemesis framework."""

from behave import given, when, then
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


@given("I am on the SauceDemo login page")
def step_navigate_to_login(context):
    """Navigate to login page."""
    # Browser is automatically managed by Nemesis
    context.login_page = LoginPage(context.page, context.config)
    context.login_page.open()


@when('I enter username "{username}"')
def step_enter_username(context, username):
    """Enter username."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.config)
    context.login_page.enter_username(username)


@when('I enter password "{password}"')
def step_enter_password(context, password):
    """Enter password."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.config)
    context.login_page.enter_password(password)


@when("I click the login button")
def step_click_login(context):
    """Click login button."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.config)
    context.login_page.click_login()


@then("I should be redirected to the inventory page")
def step_verify_inventory_redirect(context):
    """Verify redirect to inventory page."""
    # Browser is automatically managed by Nemesis
    context.inventory_page = InventoryPage(context.page, context.config)
    context.inventory_page.verify_page_loaded()


@then('I should see "Products" header')
def step_verify_products_header(context):
    """Verify Products header is visible."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'inventory_page'):
        context.inventory_page = InventoryPage(context.page, context.config)
    context.inventory_page.verify_products_header()


@then("the shopping cart icon should be visible")
def step_verify_cart_icon(context):
    """Verify shopping cart icon is visible."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'inventory_page'):
        context.inventory_page = InventoryPage(context.page, context.config)
    context.inventory_page.verify_cart_icon()


@then('I should see error message "{error_message}"')
def step_verify_error_message(context, error_message):
    """Verify error message is displayed."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.config)
    context.login_page.verify_error_message(error_message)


@then("I should remain on the login page")
def step_verify_remain_on_login(context):
    """Verify user remains on login page."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'login_page'):
        context.login_page = LoginPage(context.page, context.config)
    context.login_page.verify_page_loaded()
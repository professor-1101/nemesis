"""Simplified cart step definitions using Nemesis framework."""

from behave import given, when, then
from pages.cart_page import CartPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


@given('I am logged in as "{username}"')
def step_login_as_user(context, username):
    """Login with specified user."""
    # Browser is automatically managed by Nemesis
    # Use default password for all users
    password = "secret_sauce"
    
    context.login_page = LoginPage(context.page, context.test_config)
    context.login_page.open()
    context.login_page.login(username, password)


@given("I am on the inventory page")
def step_on_inventory_page(context):
    """Verify user is on inventory page."""
    # Browser is automatically managed by Nemesis
    context.inventory_page = InventoryPage(context.page, context.test_config)
    context.inventory_page.verify_page_loaded()


@when('I add "{product_name}" to cart')
def step_add_product_to_cart(context, product_name):
    """Add product to cart."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'inventory_page'):
        context.inventory_page = InventoryPage(context.page, context.test_config)
    context.inventory_page.add_product_to_cart(product_name)
    # Store product name for later verification
    context.last_added_product = product_name


@when("I click on the cart icon")
def step_click_cart_icon(context):
    """Click on cart icon."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'inventory_page'):
        context.inventory_page = InventoryPage(context.page, context.test_config)
    context.inventory_page.click_cart_icon()


@then('the cart badge should show "{count}"')
def step_verify_cart_badge(context, count):
    """Verify cart badge shows correct count."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'inventory_page'):
        context.inventory_page = InventoryPage(context.page, context.test_config)
    context.inventory_page.verify_cart_badge_count(count)


@then('I should see "{product_name}" in the cart')
def step_verify_product_in_cart(context, product_name):
    """Verify product is in cart."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'cart_page'):
        context.cart_page = CartPage(context.page, context.test_config)
    context.cart_page.verify_product_in_cart(product_name)


@then('the price should be "{price}"')
def step_verify_product_price(context, price):
    """Verify product price."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'cart_page'):
        context.cart_page = CartPage(context.page, context.test_config)
    # Get product name from context (set in previous step)
    product_name = getattr(context, 'last_added_product', 'Sauce Labs Backpack')
    context.cart_page.verify_product_price(product_name, price)


@then("the cart should be empty")
def step_verify_empty_cart(context):
    """Verify cart is empty."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'cart_page'):
        context.cart_page = CartPage(context.page, context.test_config)
    context.cart_page.verify_empty_cart()


@then("I should see cart headers")
def step_verify_cart_headers(context):
    """Verify cart headers are visible."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'cart_page'):
        context.cart_page = CartPage(context.page, context.test_config)
    context.cart_page.verify_cart_headers()


@then('the "Continue Shopping" button should be visible')
def step_verify_continue_shopping_button(context):
    """Verify Continue Shopping button is visible."""
    # Browser is automatically managed by Nemesis
    if not hasattr(context, 'cart_page'):
        context.cart_page = CartPage(context.page, context.test_config)
    context.cart_page.verify_continue_shopping_button()
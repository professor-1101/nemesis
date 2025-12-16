"""Checkout step definitions using sync Playwright API."""
from behave import given, when, then

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


@given('I have added "{product_name}" to cart')
def step_add_product_to_cart(context, product_name):
    """Add product to cart from inventory."""
    context.inventory_page = InventoryPage(context.page, context.config)
    # Use sync method directly
    context.inventory_page.add_product_to_cart(product_name)


@given("I am on the cart page")
def step_navigate_to_cart(context):
    """Navigate to cart page."""
    # Use sync method directly
    context.inventory_page.click_cart_icon()
    context.cart_page = CartPage(context.page, context.config)


@given('I click the "{button}" button')
def step_click_button_given(context, button):
    """Click specified button."""
    if button == "Checkout":
        # Use sync method directly
        context.cart_page.click_checkout()
        context.checkout_page = CheckoutPage(context.page, context.config)


@when('I enter first name "{first_name}"')
def step_enter_first_name(context, first_name):
    """Enter first name."""
    # Use sync method directly
    context.checkout_page.enter_first_name(first_name)


@when('I enter last name "{last_name}"')
def step_enter_last_name(context, last_name):
    """Enter last name."""
    # Use sync method directly
    context.checkout_page.enter_last_name(last_name)


@when('I enter postal code "{postal_code}"')
def step_enter_postal_code(context, postal_code):
    """Enter postal code."""
    # Use sync method directly
    context.checkout_page.enter_postal_code(postal_code)


@when('I click the "{button}" button')
def step_click_button_when(context, button):
    """Click specified button."""
    if button == "Continue":
        # Use sync method directly
        context.checkout_page.click_continue()
    elif button == "Finish":
        # Use sync method directly
        context.checkout_page.click_finish()


@when("I leave first name empty")
def step_leave_first_name_empty(context):
    """Leave first name field empty."""
    # Use sync method directly
    context.checkout_page.enter_first_name("")


@then("I should see the checkout overview page")
def step_verify_overview_page(context):
    """Verify checkout overview page."""
    # Use sync method directly
    is_on_page = context.checkout_page.is_on_overview_page()
    assert is_on_page, "Not on checkout overview page"


@then("I should see payment information")
def step_verify_payment_info(context):
    """Verify payment information is visible."""
    # Use sync method directly
    is_visible = context.checkout_page.is_payment_info_visible()
    assert is_visible, "Payment info not visible"


@then("I should see shipping information")
def step_verify_shipping_info(context):
    """Verify shipping information is visible."""
    # Use sync method directly
    is_visible = context.checkout_page.is_shipping_info_visible()
    assert is_visible, "Shipping info not visible"


@then('I should see "{message}" message')
def step_verify_message(context, message):
    """Verify message is displayed."""
    # Use sync method directly
    actual_message = context.checkout_page.get_complete_message()
    assert message in actual_message, f"Expected: {message}, Got: {actual_message}"


@then("I should see the Pony Express image")
def step_verify_pony_express(context):
    """Verify Pony Express image is visible."""
    # Use sync method directly
    is_visible = context.checkout_page.is_pony_express_visible()
    assert is_visible, "Pony Express image not visible"


@then('I should see error "{error_message}"')
def step_verify_error(context, error_message):
    """Verify error message."""
    # Use sync method directly
    actual_error = context.checkout_page.get_error_message()
    assert error_message in actual_error, f"Expected: {error_message}, Got: {actual_error}"


@then("I should remain on checkout information page")
def step_verify_on_checkout_info(context):
    """Verify still on checkout information page."""
    # Use sync method directly
    is_on_page = context.checkout_page.is_on_checkout_info_page()
    assert is_on_page, "Not on checkout info page"
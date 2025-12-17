"""Advanced step definitions for ReportPortal feature demonstration.

This module contains step definitions that showcase advanced ReportPortal capabilities:
- Custom metadata enrichment
- Explicit logging at various levels
- Data-driven testing support
"""

from behave import when, then


# Metadata Steps
@when('I add metadata "{key}" with value "{value}"')
def step_add_metadata(context, key, value):
    """Add custom metadata to ReportPortal test item.

    This demonstrates runtime metadata enrichment for better test traceability.

    Args:
        context: Behave context
        key: Metadata key (e.g., "test_environment", "browser_version")
        value: Metadata value
    """
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.add_metadata(key, value, level="INFO")


# Explicit Logging Steps
@when('I log message "{message}" at level "{level}"')
def step_log_message(context, message, level):
    """Log a custom message to ReportPortal at specified level.

    Supports: INFO, DEBUG, WARN, ERROR, TRACE

    Args:
        context: Behave context
        message: Message text to log
        level: Log level (INFO, DEBUG, WARN, ERROR, TRACE)
    """
    valid_levels = ["INFO", "DEBUG", "WARN", "ERROR", "TRACE"]
    log_level = level.upper() if level.upper() in valid_levels else "INFO"

    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.log_message(message, level=log_level)


# Product Sorting Steps (for data-driven examples)
@when('I sort products by "{sort_option}"')
def step_sort_products(context, sort_option):
    """Sort products by specified option.

    Args:
        context: Behave context
        sort_option: Sorting option (e.g., "Name (A to Z)", "Price (low to high)")
    """
    # Add metadata about sorting action
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.add_metadata("sort_action", sort_option)

    # Get product page
    from pages.product_page import ProductPage
    product_page = ProductPage(context.page)

    # Map sort options to values
    sort_mapping = {
        "Name (A to Z)": "az",
        "Name (Z to A)": "za",
        "Price (low to high)": "lohi",
        "Price (high to low)": "hilo",
    }

    sort_value = sort_mapping.get(sort_option)
    if sort_value:
        product_page.sort_products(sort_value)
    else:
        raise ValueError(f"Invalid sort option: {sort_option}")


@then('products should be sorted by "{sort_option}"')
def step_verify_products_sorted(context, sort_option):
    """Verify products are sorted correctly.

    Args:
        context: Behave context
        sort_option: Sorting option to verify
    """
    # Add metadata about verification
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.add_metadata("sort_verification", "started")

    from pages.product_page import ProductPage
    product_page = ProductPage(context.page)

    # Get all product names/prices
    products = product_page.get_all_products()

    # Verify sorting based on option
    if "Name" in sort_option:
        names = [p['name'] for p in products]
        if "A to Z" in sort_option:
            assert names == sorted(names), f"Products not sorted A to Z: {names}"
        else:  # Z to A
            assert names == sorted(names, reverse=True), f"Products not sorted Z to A: {names}"
    elif "Price" in sort_option:
        prices = [float(p['price'].replace('$', '')) for p in products]
        if "low to high" in sort_option:
            assert prices == sorted(prices), f"Products not sorted low to high: {prices}"
        else:  # high to low
            assert prices == sorted(prices, reverse=True), f"Products not sorted high to low: {prices}"

    # Log success
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.add_metadata("sort_verification", "passed")
        context.report_manager.log_message(f"Sort verification passed: {sort_option}", level="INFO")


# Enhanced Error Handling Steps
@then('I should see login error message')
def step_verify_login_error(context):
    """Verify login error message is displayed.

    Adds metadata about error verification.

    Args:
        context: Behave context
    """
    from pages.login_page import LoginPage
    login_page = LoginPage(context.page)

    # Check for error message
    error_visible = login_page.is_error_displayed()

    # Add metadata
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.add_metadata("error_displayed", str(error_visible))

    assert error_visible, "Login error message not displayed"

    # Log error text if available
    try:
        error_text = login_page.get_error_text()
        if hasattr(context, 'report_manager') and context.report_manager:
            context.report_manager.add_metadata("error_text", error_text)
            context.report_manager.log_message(f"Error message: {error_text}", level="WARN")
    except Exception:
        pass  # Error text not available


# Enhanced Cart Verification
@then('I should see {count:d} items in the cart')
def step_verify_cart_count_enhanced(context, count):
    """Verify cart item count with metadata logging.

    Args:
        context: Behave context
        count: Expected number of items
    """
    from pages.product_page import ProductPage
    product_page = ProductPage(context.page)

    cart_count = product_page.get_cart_count()

    # Add metadata
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.add_metadata("expected_cart_count", str(count))
        context.report_manager.add_metadata("actual_cart_count", str(cart_count))

    assert cart_count == count, f"Expected {count} items in cart, found {cart_count}"

    # Log success
    if hasattr(context, 'report_manager') and context.report_manager:
        context.report_manager.log_message(f"Cart count verified: {count} items", level="INFO")

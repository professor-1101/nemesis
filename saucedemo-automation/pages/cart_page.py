"""Cart page object using sync Playwright API."""
from typing import Any

from playwright.sync_api import Page

from pages.base_page import BasePage


class CartPage(BasePage):
    """Shopping cart page interactions using sync Playwright API."""

    # Selectors
    CART_ITEM = ".cart_item"
    ITEM_NAME = ".inventory_item_name"
    ITEM_PRICE = ".inventory_item_price"
    CONTINUE_SHOPPING_BUTTON = "#continue-shopping"
    CHECKOUT_BUTTON = "#checkout"
    QTY_HEADER = ".cart_quantity_label"
    DESC_HEADER = ".cart_desc_label"
    REMOVE_BUTTON = "[data-test^='remove']"

    def __init__(self, page: Page, config: Any) -> None:
        super().__init__(page, config)

    def is_loaded(self) -> bool:
        """Check if cart page is loaded synchronously."""
        return self.is_visible(self.CHECKOUT_BUTTON)

    def is_cart_empty(self) -> bool:
        """Check if cart has no items synchronously."""
        return not self.is_visible(self.CART_ITEM)
    
    def verify_empty_cart(self) -> None:
        """Verify cart is empty synchronously."""
        if not self.is_cart_empty():
            raise Exception("Cart is not empty")

    def get_cart_items_count(self) -> int:
        """Get number of items in cart synchronously."""
        return self.page.locator(self.CART_ITEM).count()

    def is_product_in_cart(self, product_name: str) -> bool:
        """Check if product is in cart synchronously."""
        return self.is_visible(f"text={product_name}")
    
    def verify_product_in_cart(self, product_name: str) -> None:
        """Verify product is in cart synchronously."""
        if not self.is_product_in_cart(product_name):
            raise Exception(f"Product '{product_name}' not found in cart")

    def get_product_price(self, product_name: str) -> str:
        """Get product price from cart synchronously."""
        item = self.page.locator(self.CART_ITEM).filter(has_text=product_name)
        return item.locator(self.ITEM_PRICE).text_content() or ""
    
    def verify_product_price(self, product_name: str, expected_price: str) -> None:
        """Verify product price in cart synchronously."""
        actual_price = self.get_product_price(product_name)
        if actual_price != expected_price:
            raise Exception(f"Price mismatch for '{product_name}'. Expected: {expected_price}, Actual: {actual_price}")

    def click_checkout(self) -> None:
        """Click checkout button synchronously."""
        self.click(self.CHECKOUT_BUTTON)

    def click_continue_shopping(self) -> None:
        """Click continue shopping button synchronously."""
        self.click(self.CONTINUE_SHOPPING_BUTTON)

    def is_continue_shopping_visible(self) -> bool:
        """Check if continue shopping button is visible synchronously."""
        return self.is_visible(self.CONTINUE_SHOPPING_BUTTON)
    
    def verify_continue_shopping_button(self) -> None:
        """Verify continue shopping button is visible synchronously."""
        if not self.is_continue_shopping_visible():
            raise Exception("Continue Shopping button is not visible")

    def are_headers_visible(self) -> bool:
        """Check if QTY and DESCRIPTION headers are visible synchronously."""
        qty_visible = self.is_visible(self.QTY_HEADER)
        desc_visible = self.is_visible(self.DESC_HEADER)
        return qty_visible and desc_visible
    
    def verify_cart_headers(self) -> None:
        """Verify cart headers are visible synchronously."""
        if not self.are_headers_visible():
            raise Exception("Cart headers (QTY and DESCRIPTION) are not visible")
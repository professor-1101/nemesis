"""Inventory page object using sync Playwright API."""
from typing import Any

from playwright.sync_api import Page

from pages.base_page import BasePage


class InventoryPage(BasePage):
    """Inventory page interactions using sync Playwright API."""

    # Selectors
    PAGE_TITLE = ".title"
    SHOPPING_CART_ICON = ".shopping_cart_link"
    CART_BADGE = ".shopping_cart_badge"
    INVENTORY_ITEM = ".inventory_item"
    ADD_TO_CART_BUTTON = "[data-test^='add-to-cart']"

    def __init__(self, page: Page, config: Any) -> None:
        super().__init__(page, config)

    def is_loaded(self) -> bool:
        """Check if inventory page is loaded synchronously."""
        return self.is_visible(self.PAGE_TITLE)
    
    def verify_page_loaded(self) -> None:
        """Verify inventory page is loaded synchronously."""
        if not self.is_loaded():
            raise Exception("Inventory page not loaded")
    
    def verify_products_header(self) -> None:
        """Verify Products header is visible synchronously."""
        if not self.is_visible(self.PAGE_TITLE):
            raise Exception("Products header not visible")
        title_text = self.get_text(self.PAGE_TITLE)
        if "Products" not in title_text:
            raise Exception(f"Products header not found. Found: {title_text}")
    
    def verify_cart_icon(self) -> None:
        """Verify shopping cart icon is visible synchronously."""
        if not self.is_cart_icon_visible():
            raise Exception("Shopping cart icon not visible")

    def get_page_title(self) -> str:
        """Get page title text synchronously."""
        return self.get_text(self.PAGE_TITLE)

    def is_cart_icon_visible(self) -> bool:
        """Check if cart icon is visible synchronously."""
        return self.is_visible(self.SHOPPING_CART_ICON)

    def add_product_to_cart(self, product_name: str) -> None:
        """Add product to cart by name synchronously."""
        product_id = self._get_product_id(product_name)
        button_selector = f"[data-test='add-to-cart-{product_id}']"
        self.click(button_selector)

    def get_cart_count(self) -> str:
        """Get cart badge count synchronously."""
        if self.is_visible(self.CART_BADGE):
            return self.get_text(self.CART_BADGE)
        return "0"
    
    def verify_cart_badge_count(self, expected_count: str) -> None:
        """Verify cart badge shows expected count synchronously."""
        actual_count = self.get_cart_count()
        if actual_count != expected_count:
            raise Exception(f"Cart badge count mismatch. Expected: {expected_count}, Actual: {actual_count}")

    def click_cart_icon(self) -> None:
        """Click shopping cart icon synchronously."""
        self.click(self.SHOPPING_CART_ICON)

    def _get_product_id(self, product_name: str) -> str:
        """Convert product name to ID format."""
        return product_name.lower().replace(" ", "-")
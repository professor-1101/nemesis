"""Cart page object using Clean Architecture.

This refactored CartPage demonstrates:
- Using IPage interface through BasePage
- Framework independence
- Clean separation of concerns
"""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


class CartPage(BasePage):
    """
    Shopping cart page interactions using IPage interface.

    Clean Architecture:
    - Depends on IPage interface, not Playwright
    - Framework-independent
    - Business logic in page object
    """

    # Selectors
    CART_ITEM = ".cart_item"
    ITEM_NAME = ".inventory_item_name"
    ITEM_PRICE = ".inventory_item_price"
    CONTINUE_SHOPPING_BUTTON = "#continue-shopping"
    CHECKOUT_BUTTON = "#checkout"
    QTY_HEADER = ".cart_quantity_label"
    DESC_HEADER = ".cart_desc_label"
    REMOVE_BUTTON = "[data-test^='remove']"

    def __init__(self, page: IPage, config: dict) -> None:
        """
        Initialize cart page

        Args:
            page: IPage interface implementation
            config: Configuration dictionary
        """
        super().__init__(page, config)

    def is_loaded(self) -> bool:
        """Check if cart page is loaded"""
        return self.is_visible(self.CHECKOUT_BUTTON)

    def is_cart_empty(self) -> bool:
        """Check if cart has no items"""
        return not self.is_visible(self.CART_ITEM)

    def verify_empty_cart(self) -> None:
        """Verify cart is empty"""
        if not self.is_cart_empty():
            raise AssertionError("Cart is not empty")

    def get_cart_items_count(self) -> int:
        """
        Get number of items in cart

        Uses underlying Playwright page for locator.count()
        For production: extend IPage interface with count methods
        """
        if self._playwright_page:
            return self._playwright_page.locator(self.CART_ITEM).count()
        else:
            # Fallback: check if at least one item exists
            return 1 if self.is_visible(self.CART_ITEM) else 0

    def is_product_in_cart(self, product_name: str) -> bool:
        """Check if product is in cart"""
        return self.is_visible(f"text={product_name}")

    def verify_product_in_cart(self, product_name: str) -> None:
        """Verify product is in cart"""
        if not self.is_product_in_cart(product_name):
            raise AssertionError(f"Product '{product_name}' not found in cart")

    def get_product_price(self, product_name: str) -> str:
        """
        Get product price from cart

        Uses underlying Playwright page for advanced filtering
        For production: extend IPage interface with filter/has_text
        """
        if self._playwright_page:
            item = self._playwright_page.locator(self.CART_ITEM).filter(
                has_text=product_name
            )
            return item.locator(self.ITEM_PRICE).text_content() or ""
        else:
            # Fallback: basic implementation
            return self.get_text(self.ITEM_PRICE)

    def verify_product_price(self, product_name: str, expected_price: str) -> None:
        """Verify product price in cart"""
        actual_price = self.get_product_price(product_name)
        if actual_price != expected_price:
            raise AssertionError(
                f"Price mismatch for '{product_name}'. "
                f"Expected: {expected_price}, Actual: {actual_price}"
            )

    def click_checkout(self) -> None:
        """Click checkout button"""
        self.click(self.CHECKOUT_BUTTON)

    def click_continue_shopping(self) -> None:
        """Click continue shopping button"""
        self.click(self.CONTINUE_SHOPPING_BUTTON)

    def is_continue_shopping_visible(self) -> bool:
        """Check if continue shopping button is visible"""
        return self.is_visible(self.CONTINUE_SHOPPING_BUTTON)

    def verify_continue_shopping_button(self) -> None:
        """Verify continue shopping button is visible"""
        if not self.is_continue_shopping_visible():
            raise AssertionError("Continue Shopping button is not visible")

    def are_headers_visible(self) -> bool:
        """Check if QTY and DESCRIPTION headers are visible"""
        qty_visible = self.is_visible(self.QTY_HEADER)
        desc_visible = self.is_visible(self.DESC_HEADER)
        return qty_visible and desc_visible

    def verify_cart_headers(self) -> None:
        """Verify cart headers are visible"""
        if not self.are_headers_visible():
            raise AssertionError("Cart headers (QTY and DESCRIPTION) are not visible")

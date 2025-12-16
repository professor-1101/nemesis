"""Checkout page object using Clean Architecture.

This refactored CheckoutPage demonstrates:
- Using IPage interface through BasePage
- Framework independence
- Clean separation of concerns
"""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """
    Checkout page interactions using IPage interface.

    Clean Architecture:
    - Depends on IPage interface, not Playwright
    - Framework-independent
    - Business logic in page object
    """

    # Selectors - Step 1 (Information)
    FIRST_NAME_INPUT = "#first-name"
    LAST_NAME_INPUT = "#last-name"
    POSTAL_CODE_INPUT = "#postal-code"
    CONTINUE_BUTTON = "#continue"
    ERROR_MESSAGE = "[data-test='error']"

    # Selectors - Step 2 (Overview)
    PAYMENT_INFO = ".summary_info_label:has-text('Payment Information')"
    SHIPPING_INFO = ".summary_info_label:has-text('Shipping Information')"
    FINISH_BUTTON = "#finish"

    # Selectors - Complete
    COMPLETE_HEADER = ".complete-header"
    PONY_EXPRESS_IMAGE = ".pony_express"

    def __init__(self, page: IPage, config: dict) -> None:
        """
        Initialize checkout page

        Args:
            page: IPage interface implementation
            config: Configuration dictionary
        """
        super().__init__(page, config)

    def enter_first_name(self, first_name: str) -> None:
        """Enter first name"""
        self.fill(self.FIRST_NAME_INPUT, first_name)

    def enter_last_name(self, last_name: str) -> None:
        """Enter last name"""
        self.fill(self.LAST_NAME_INPUT, last_name)

    def enter_postal_code(self, postal_code: str) -> None:
        """Enter postal code"""
        self.fill(self.POSTAL_CODE_INPUT, postal_code)

    def click_continue(self) -> None:
        """Click continue button"""
        self.click(self.CONTINUE_BUTTON)

    def fill_checkout_info(
        self, first_name: str, last_name: str, postal_code: str
    ) -> None:
        """
        Fill all checkout information

        Business logic: Complete checkout form flow
        """
        self.enter_first_name(first_name)
        self.enter_last_name(last_name)
        self.enter_postal_code(postal_code)

    def get_error_message(self) -> str:
        """Get error message"""
        return self.get_text(self.ERROR_MESSAGE)

    def is_on_checkout_info_page(self) -> bool:
        """Check if on checkout info page"""
        return self.is_visible(self.FIRST_NAME_INPUT)

    def is_on_overview_page(self) -> bool:
        """Check if on checkout overview page"""
        return self.is_visible(self.FINISH_BUTTON)

    def is_payment_info_visible(self) -> bool:
        """Check if payment info is visible"""
        return self.is_visible(self.PAYMENT_INFO)

    def is_shipping_info_visible(self) -> bool:
        """Check if shipping info is visible"""
        return self.is_visible(self.SHIPPING_INFO)

    def click_finish(self) -> None:
        """Click finish button"""
        self.click(self.FINISH_BUTTON)

    def is_order_complete(self) -> bool:
        """Check if order is complete"""
        return self.is_visible(self.COMPLETE_HEADER)

    def get_complete_message(self) -> str:
        """Get completion message"""
        return self.get_text(self.COMPLETE_HEADER)

    def is_pony_express_visible(self) -> bool:
        """Check if pony express image is visible"""
        return self.is_visible(self.PONY_EXPRESS_IMAGE)

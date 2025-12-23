"""Applicant registration page object for PostBank application."""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


class ApplicantPage(BasePage):
    """
    Applicant registration page interactions using IPage interface.
    """

    # Selectors - باید با selectors واقعی جایگزین شوند
    ADD_BUTTON = "#add-button"
    SAVE_BUTTON = "#save-button"
    OPERATIONS_BUTTON = "#operations-button"
    PERSON_INFO_PAGE = ".person-info-page"
    APPLICANT_PAGE = ".applicant-page"
    FINAL_RESULT_DROPDOWN = "#final-result-dropdown"
    ERROR_MESSAGE = ".error-message"
    SUCCESS_MESSAGE = ".success-message"

    def __init__(self, page: IPage, config: dict) -> None:
        """Initialize applicant page"""
        super().__init__(page, config)

    def click_add_button(self) -> None:
        """Click add button"""
        self.click(self.ADD_BUTTON)

    def click_save_button(self) -> None:
        """Click save button"""
        self.click(self.SAVE_BUTTON)

    def click_operations_button(self) -> None:
        """Click operations button"""
        self.click(self.OPERATIONS_BUTTON)

    def fill_field(self, field_name: str, value: str) -> None:
        """Fill a field by name"""
        # این باید با selector واقعی جایگزین شود
        selector = f"[name='{field_name}']"
        self.fill(selector, value)

    def fill_required_fields(self, fields: dict) -> None:
        """Fill all required fields"""
        for field_name, value in fields.items():
            self.fill_field(field_name, value)

    def select_final_result(self, result: str) -> None:
        """Select final result from dropdown"""
        self.select_option(self.FINAL_RESULT_DROPDOWN, result)

    def is_on_person_info_page(self) -> bool:
        """Check if on person info page"""
        return self.is_visible(self.PERSON_INFO_PAGE)

    def is_on_applicant_page(self) -> bool:
        """Check if on applicant page"""
        return self.is_visible(self.APPLICANT_PAGE)

    def get_error_message(self) -> str:
        """Get error message text"""
        return self.get_text(self.ERROR_MESSAGE)

    def is_error_visible(self) -> bool:
        """Check if error message is visible"""
        return self.is_visible(self.ERROR_MESSAGE)

    def get_success_message(self) -> str:
        """Get success message text"""
        return self.get_text(self.SUCCESS_MESSAGE)

    def verify_error_message(self, expected_message: str) -> None:
        """Verify error message is displayed"""
        if not self.is_error_visible():
            raise AssertionError("Error message not visible")

        actual_message = self.get_error_message()
        if expected_message not in actual_message:
            raise AssertionError(
                f"Expected error message '{expected_message}' not found. "
                f"Found: '{actual_message}'"
            )




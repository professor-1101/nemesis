"""Applicant registration page object for PostBank application."""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage
from utils.persian_data_generator import PersianDataGenerator


class ApplicantRegistrationPage(BasePage):
    """
    Applicant registration page interactions using IPage interface.
    """

    # Menu selectors
    MENU_ITEMS = ".menuItems"
    MENU_BUTTON = ".menu-button"
    APPLICANT_INFO_MENU = "text=اطلاعات متقاضیان"
    APPLICANT_REGISTRATION_SUBMENU = "text=ثبت متقاضی"

    # Page elements
    ADD_BUTTON = "a.k-button.AddBtn[data-testid='addBtn-Grid_1_OrgUnitPersonCRel'], button:has-text('اضافه کردن'), [data-testid*='add'], .add-button"
    SAVE_BUTTON = "[data-testid='button-ذخیره'], button:has-text('ذخیره'), [data-testid*='save'], .save-button"

    # Second add button on applicant page - use same selector as first button
    SECOND_ADD_BUTTON = "a.k-button.AddBtn[data-testid='addBtn-Grid_1_OrgUnitPersonCRel'], .AddBtn, [data-testid='addBtn-Grid_1_OrgUnitPersonCRel']"

    # Breadcrumbs
    APPLICANT_BREADCRUMB = ".breadcrumb-item:has-text('متقاضی'), .Breadcrumb:has-text('متقاضی')"
    PERSONAL_INFO_BREADCRUMB = "[data-testid*='breadcrumb'], .k-link:has-text('اطلاعات شخص'), .breadcrumb-item:has-text('اطلاعات شخص'), :has-text('اطلاعات شخص'), .Breadcrumb:has-text('متقاضی')"

    # Form fields - Personal Information
    # Required fields
    PROVINCE_DROPDOWN = "[data-testid='KendoFormDropDownTree-Prop_5_CountryDivisionsRel'] .k-dropdown-wrap, [data-testid*='province'], select[name*='province'], select[placeholder*='استان']"
    NATIONAL_CODE_FIELD = "[data-testid='KendoFormInput-Prop_10_NationalCode'] input, [data-testid*='nationalCode'], input[name*='nationalCode'], input[placeholder*='کد ملی']"
    BIRTH_DATE_FIELD = "[data-testid='FormDatePicker-Prop_12_BirthDate'] input, [data-testid*='birthDate'], input[name*='birthDate'], input[type='date']"
    NAME_FIELD = "[data-testid='KendoFormInput-Prop_20_FirstName'] input, [data-testid*='name'], input[name*='name'], input[placeholder*='نام']"
    ID_NUMBER_FIELD = "[data-testid='KendoFormInput-Prop_21_BirthCertificateNo'] input, [data-testid*='idNumber'], input[name*='idNumber'], input[placeholder*='شماره شناسنامه']"
    GENDER_DROPDOWN = "[data-testid='KendoFormComboBox-Prop_22_GenderCID'] .k-dropdown-wrap, [data-testid*='gender'], select[name*='gender'], select[placeholder*='جنسیت']"
    BIRTH_PLACE_DROPDOWN = "[data-testid='KendoFormDropDownTree-Prop_23_BirthPlaceRel'] .k-dropdown-wrap, [data-testid*='birthPlace'], select[name*='birthPlace'], select[placeholder*='محل تولد']"
    FAMILY_NAME_FIELD = "[data-testid='KendoFormInput-Prop_26_LastName'] input, [data-testid*='family'], input[name*='family'], input[placeholder*='نام خانوادگی']"
    FATHER_NAME_FIELD = "[data-testid='KendoFormInput-Prop_27_FatherName'] input, [data-testid*='fatherName'], input[name*='fatherName'], input[placeholder*='نام پدر']"
    ISSUE_PLACE_DROPDOWN = "[data-testid='KendoFormDropDownTree-Prop_29_IssuePlaceRel'] .k-dropdown-wrap, [data-testid*='issuePlace'], select[name*='issuePlace'], select[placeholder*='محل صدور']"

    # Optional fields
    ACTIVE_CHECKBOX = "[data-testid='KendoFormCheckbox-Prop_49_IsActive'] input, [data-testid*='active'], input[name*='active'], .active-checkbox"
    DESCRIPTION_FIELD = "[data-testid='KendoFormTextArea-Prop_53_PersonnelDescription'] textarea, textarea[name*='description'], textarea[placeholder*='توضیحات']"

    # Messages
    SUCCESS_MESSAGE = "text=سند با موفقیت ذخیره شد, .success-message, .alert-success"
    ERROR_MESSAGE = ".error-message, .alert-danger, [role='alert']"

    def __init__(self, page: IPage, config: dict) -> None:
        """Initialize applicant registration page"""
        super().__init__(page, config)

    def navigate_to_applicant_registration(self) -> None:
        """
        Navigate to applicant registration page through menu.

        Clean implementation:
        - Uses proper selectors and waits
        - No hard-coded sleep delays
        - Verifies page loaded before returning
        """
        try:
            # Expand menu
            self._playwright_page.click(self.MENU_BUTTON)
            self._playwright_page.wait_for_selector(self.APPLICANT_INFO_MENU, state="visible")

            # Navigate to applicant info menu
            self._playwright_page.click(self.APPLICANT_INFO_MENU)
            self._playwright_page.wait_for_selector(self.APPLICANT_REGISTRATION_SUBMENU, state="visible")

            # Click registration submenu
            self._playwright_page.click(self.APPLICANT_REGISTRATION_SUBMENU)

            # Wait for page to load (verify add button visible)
            self._playwright_page.wait_for_selector(self.ADD_BUTTON, state="visible", timeout=10000)

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self._save_debug_info(f"Failed to navigate to applicant registration: {e}")
            raise AssertionError(f"Could not navigate to applicant registration page: {e}")

    def click_add_button(self) -> None:
        """
        Click the add button to create new applicant.

        Waits for applicant breadcrumb to appear after click.
        """
        try:
            self.click(self.ADD_BUTTON, timeout=5000)
            # Wait for navigation to complete (breadcrumb visible)
            self._playwright_page.wait_for_selector(self.APPLICANT_BREADCRUMB, state="visible", timeout=5000)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self._save_debug_info(f"Failed to click add button: {e}")
            raise AssertionError(f"Could not click add button: {e}")

    def click_second_add_button(self) -> None:
        """
        Click the second add button on the applicant page.

        Waits for personal info form to load after click.
        """
        try:
            self.click(self.SECOND_ADD_BUTTON, timeout=5000)
            # Wait for personal info form to load
            self._playwright_page.wait_for_selector(self.NATIONAL_CODE_FIELD, state="visible", timeout=5000)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self._save_debug_info(f"Failed to click second add button: {e}")
            raise AssertionError(f"Could not click second add button: {e}")

    def verify_applicant_breadcrumb_visible(self) -> bool:
        """Verify that applicant breadcrumb is visible"""
        try:
            return self.is_visible(self.APPLICANT_BREADCRUMB, timeout=5000)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return False

    def verify_personal_info_breadcrumb_visible(self) -> bool:
        """Verify that personal info form is loaded (breadcrumb or form presence)"""
        try:
            # Check for breadcrumb or form elements
            return (
                self.is_visible(self.PERSONAL_INFO_BREADCRUMB, timeout=3000) or
                self.is_visible(self.NATIONAL_CODE_FIELD, timeout=3000) or
                self.is_visible(self.NAME_FIELD, timeout=3000)
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return False

    def fill_personal_info_form(self, **kwargs) -> None:
        """
        Fill the complete personal information form with random Persian data.

        Clean implementation:
        - Uses PersianDataGenerator for test data
        - Simplified fill logic (uses _playwright_page directly)
        - No code duplication

        Args:
            **kwargs: Override default random data with specific values

        Example:
            >>> page.fill_personal_info_form(name="علی", family_name="احمدی")
        """
        try:
            # Generate random data using utility class
            form_data = PersianDataGenerator.generate_personal_data(**kwargs)

            # Fill all required fields using Playwright page directly
            # Province
            self.select_kendo_dropdown_option(self.PROVINCE_DROPDOWN, form_data['province'])

            # Text fields
            self._playwright_page.fill(self.NATIONAL_CODE_FIELD, form_data['national_code'])
            self._playwright_page.fill(self.BIRTH_DATE_FIELD, form_data['birth_date'])
            self._playwright_page.fill(self.NAME_FIELD, form_data['name'])
            self._playwright_page.fill(self.ID_NUMBER_FIELD, form_data['id_number'])
            self._playwright_page.fill(self.FAMILY_NAME_FIELD, form_data['family_name'])
            self._playwright_page.fill(self.FATHER_NAME_FIELD, form_data['father_name'])

            # Dropdowns
            self.select_kendo_dropdown_option(self.GENDER_DROPDOWN, form_data['gender'])

            # Tree dropdowns (province > city)
            self.select_kendo_dropdown_tree_option(
                self.BIRTH_PLACE_DROPDOWN,
                form_data['birth_place_province'],
                form_data['birth_place']
            )
            self.select_kendo_dropdown_tree_option(
                self.ISSUE_PLACE_DROPDOWN,
                form_data['issue_place_province'],
                form_data['issue_place']
            )

            # Optional fields
            if form_data.get('active', True):
                self.check(self.ACTIVE_CHECKBOX)

            if form_data.get('description'):
                self.fill(self.DESCRIPTION_FIELD, form_data['description'])

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self._save_debug_info(f"Failed to fill personal info form: {e}")
            raise AssertionError(f"Could not fill personal info form: {e}")

    def select_exam_result(self, result: str) -> None:
        """
        Select exam result in dropdown.

        Args:
            result: "قبول" or "رد"
        """
        try:
            self.select_option(self.RESULT_DROPDOWN, result)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self._save_debug_info(f"Failed to select exam result '{result}': {e}")
            raise AssertionError(f"Could not select exam result '{result}': {e}")

    def click_save_button(self) -> None:
        """
        Click the save button.

        Waits for either success or error message to appear.
        """
        try:
            self.click(self.SAVE_BUTTON, timeout=5000)
            # Wait for response (success or error message)
            self._playwright_page.wait_for_selector(
                f"{self.SUCCESS_MESSAGE}, {self.ERROR_MESSAGE}",
                state="visible",
                timeout=10000
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self._save_debug_info(f"Failed to click save button: {e}")
            raise AssertionError(f"Could not click save button: {e}")

    def is_success_message_displayed(self) -> bool:
        """Check if success message is displayed"""
        try:
            return self.is_visible(self.SUCCESS_MESSAGE, timeout=5000)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return False

    def get_success_message(self) -> str:
        """Get success message text"""
        try:
            return self.get_text(self.SUCCESS_MESSAGE)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return ""

    def is_error_message_displayed(self) -> bool:
        """Check if error message is displayed"""
        try:
            return self.is_visible(self.ERROR_MESSAGE, timeout=5000)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return False

    def get_error_message(self) -> str:
        """Get error message text"""
        try:
            return self.get_text(self.ERROR_MESSAGE)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return ""

    def is_page_loaded(self) -> bool:
        """Check if applicant registration page is loaded"""
        try:
            # Check for presence of key elements
            return (
                self.is_visible(self.ADD_BUTTON, timeout=3000) or
                self.is_visible("text=ثبت متقاضی", timeout=3000)
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return False

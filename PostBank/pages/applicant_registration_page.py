"""Applicant registration page object for PostBank application."""

from nemesis.domain.ports import IPage
from pages.base_page import BasePage


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
        """
        try:
            # First, click the menu button to expand the menu
            self._playwright_page.click(self.MENU_BUTTON)

            # Then click on "اطلاعات متقاضیان" menu
            self._playwright_page.click(self.APPLICANT_INFO_MENU)

            # Finally click on "ثبت متقاضی" submenu
            self._playwright_page.click(self.APPLICANT_REGISTRATION_SUBMENU)

            # Wait for page to load
            import time
            time.sleep(3)

        except Exception as e:
            self._save_debug_info(f"Failed to navigate to applicant registration: {e}")
            raise AssertionError(f"Could not navigate to applicant registration page: {e}")

    def click_add_button(self) -> None:
        """Click the add button to create new applicant"""
        try:
            self.click(self.ADD_BUTTON, timeout=5000)
            # Wait for page to load
            import time
            time.sleep(2)
        except Exception as e:
            self._save_debug_info(f"Failed to click add button: {e}")
            raise AssertionError(f"Could not click add button: {e}")

    def click_second_add_button(self) -> None:
        """Click the second add button on the applicant page"""
        try:
            self.click(self.SECOND_ADD_BUTTON, timeout=5000)
            # Wait for page to load
            import time
            time.sleep(2)
        except Exception as e:
            self._save_debug_info(f"Failed to click second add button: {e}")
            raise AssertionError(f"Could not click second add button: {e}")

    def verify_applicant_breadcrumb_visible(self) -> bool:
        """Verify that applicant breadcrumb is visible"""
        try:
            return self.is_visible(self.APPLICANT_BREADCRUMB, timeout=5000)
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
        except Exception:
            return False

    def fill_personal_info_form(self, **kwargs) -> None:
        """
        Fill the complete personal information form with random Persian data.

        Args:
            **kwargs: Override default random data with specific values
        """
        try:
            # Generate random data
            form_data = self._generate_random_personal_data()
            form_data.update(kwargs)  # Override with provided values

            # Fill all required fields
            # Province: select the province directly (it's a final tree item, no need to expand)
            self.select_kendo_dropdown_option(self.PROVINCE_DROPDOWN, form_data['province'])
            if self._playwright_page:
                self._playwright_page.fill(self.NATIONAL_CODE_FIELD, form_data['national_code'])
                self._playwright_page.fill(self.BIRTH_DATE_FIELD, form_data['birth_date'])
                self._playwright_page.fill(self.NAME_FIELD, form_data['name'])
                self._playwright_page.fill(self.ID_NUMBER_FIELD, form_data['id_number'])
            else:
                self.fill(self.NATIONAL_CODE_FIELD, form_data['national_code'])
                self.fill(self.BIRTH_DATE_FIELD, form_data['birth_date'])
                self.fill(self.NAME_FIELD, form_data['name'])
                self.fill(self.ID_NUMBER_FIELD, form_data['id_number'])
            self.select_kendo_dropdown_option(self.GENDER_DROPDOWN, form_data['gender'])
            # Birth place and issue place are tree dropdowns (province > city)
            self.select_kendo_dropdown_tree_option(self.BIRTH_PLACE_DROPDOWN, form_data['birth_place_province'], form_data['birth_place'])
            if self._playwright_page:
                self._playwright_page.fill(self.FAMILY_NAME_FIELD, form_data['family_name'])
                self._playwright_page.fill(self.FATHER_NAME_FIELD, form_data['father_name'])
            else:
                self.fill(self.FAMILY_NAME_FIELD, form_data['family_name'])
                self.fill(self.FATHER_NAME_FIELD, form_data['father_name'])
            self.select_kendo_dropdown_tree_option(self.ISSUE_PLACE_DROPDOWN, form_data['issue_place_province'], form_data['issue_place'])

            # Set active checkbox (default to True)
            if form_data.get('active', True):
                self.check(self.ACTIVE_CHECKBOX)

            # Fill description field (optional)
            if 'description' in form_data and form_data['description']:
                self.fill(self.DESCRIPTION_FIELD, form_data['description'])

        except Exception as e:
            self._save_debug_info(f"Failed to fill personal info form: {e}")
            raise AssertionError(f"Could not fill personal info form: {e}")

    def _generate_random_personal_data(self) -> dict:
        """
        Generate random Persian personal data for form filling.

        Returns:
            dict: Random personal data
        """
        import random
        from datetime import datetime, timedelta

        # Persian provinces
        provinces = [
            "تهران", "اصفهان", "فارس", "خوزستان", "مازندران", "گیلان",
            "آذربایجان شرقی", "آذربایجان غربی", "کرمان", "سیستان و بلوچستان",
            "خراسان رضوی", "خراسان شمالی", "خراسان جنوبی", "البرز",
            "قزوین", "زنجان", "مرکزی", "همدان", "کردستان", "کرمانشاه",
            "لرستان", "ایلام", "چهارمحال و بختیاری", "کهگیلویه و بویراحمد",
            "بوشهر", "هرمزگان", "یزد", "سمنان", "گلستان", "اردبیل"
        ]

        # Persian cities (for birth place and issue place) - using more common cities
        cities = [
            "تهران", "اصفهان", "شیراز", "مشهد", "کرج", "اهواز", "رشت", "تبریز",
            "کرمان", "یزد", "قم", "اراک", "زنجان", "همدان", "کرمانشاه", "خرم آباد",
            "سنندج", "بجنورد", "ساری", "گرگان", "اردبیل", "بندرعباس", "زاهدان", "یاسوج"
        ]

        # Persian first names
        male_names = ["احمد", "محمد", "علی", "حسین", "حسن", "رضا", "مهدی", "امیر", "سعید", "حمید", "اکبر", "جعفر", "مرتضی", "ناصر", "فرید"]
        female_names = ["فاطمه", "زهرا", "مریم", "نازنین", "سمانه", "ملیحه", "زینب", "فائزه", "مینا", "نیلوفر", "شیرین", "مژگان", "لیلا", "سپیده", "رقیه"]

        # Persian last names
        last_names = ["احمدی", "رضایی", "کریمی", "حسینی", "محمدی", "علوی", "شیرازی", "تهرانی", "اصفهانی", "مشهدی", "کرمانی", "تبریزی", "اهوازی", "رشت"]

        # Father names
        father_names = ["حسین", "احمد", "محمد", "علی", "حسن", "رضا", "محمود", "اکبر", "جعفر", "ناصر", "فرید", "عباس", "جواد", "کاظم", "غلام"]

        # Generate birth date (more than 18 years old) in Persian/Jalali format
        def gregorian_to_jalali(gy, gm, gd):
            """Convert Gregorian date to Jalali (Persian) date"""
            g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
            if gy > 1600:
                jy = 979
                gy -= 1600
            else:
                jy = 0
                gy -= 621
            gy2 = 366 if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0) else 365
            days = (gy - 1) * 365 + (gy // 4) - (gy // 100) + (gy // 400) + g_d_m[gm - 1] + gd
            if gm > 2 and gy2 == 366:
                days += 1
            jy += 33 * (days // 12053)
            days %= 12053
            jy += 4 * (days // 1461)
            days %= 1461
            if days > 365:
                jy += (days - 1) // 365
                days = (days - 1) % 365
            if days < 186:
                jm = 1 + days // 31
                jd = 1 + days % 31
            else:
                jm = 7 + (days - 186) // 30
                jd = 1 + (days - 186) % 30
            return jy, jm, jd

        # Generate birth date (more than 18 years old)
        today = datetime.now()
        # Minimum age: 18 years + 1 day (more than 18 years)
        max_age_date = today - timedelta(days=18*365 + 1)  # More than 18 years ago
        min_age_date = today - timedelta(days=65*365)  # 65 years ago

        birth_date = min_age_date + timedelta(days=random.randint(0, (max_age_date - min_age_date).days))
        # Convert to Jalali
        jy, jm, jd = gregorian_to_jalali(birth_date.year, birth_date.month, birth_date.day)
        # Format as ۱۴۰۴/۰۹/۲۹
        birth_date_str = f"{jy}/{jm:02d}/{jd:02d}"

        # Generate national code (10 digits, valid checksum)
        def generate_national_code():
            # Generate first 9 digits
            code = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            # Calculate checksum
            total = 0
            for i, digit in enumerate(code):
                total += int(digit) * (10 - i)
            checksum = total % 11
            if checksum < 2:
                control_digit = checksum
            else:
                control_digit = 11 - checksum
            # Ensure 10 digits
            national_code = code + str(control_digit)
            if len(national_code) != 10:
                # Regenerate if not 10 digits (shouldn't happen, but safety check)
                return generate_national_code()
            return national_code

        # Random selections
        gender = random.choice(["مرد", "زن"])
        province = random.choice(provinces)
        # For birth place and issue place: select random province and city
        birth_place_province = random.choice(provinces)
        birth_place = random.choice(cities)
        issue_place_province = random.choice(provinces)
        issue_place = random.choice(cities)

        if gender == "مرد":
            first_name = random.choice(male_names)
        else:
            first_name = random.choice(female_names)

        last_name = random.choice(last_names)
        father_name = random.choice(father_names)

        # ID number (random 8-10 digits)
        id_number = str(random.randint(10000000, 9999999999))

        national_code = generate_national_code()
        return {
            'province': province,
            'national_code': national_code,
            'birth_date': birth_date_str,
            'name': first_name,
            'id_number': id_number,
            'gender': gender,
            'birth_place_province': birth_place_province,
            'birth_place': birth_place,  # City for birth place
            'family_name': last_name,
            'father_name': father_name,
            'issue_place_province': issue_place_province,
            'issue_place': issue_place,  # City for issue place
            'active': True,
            'description': f"متقاضی {first_name} {last_name} - کد ملی {national_code}"
        }

    def select_exam_result(self, result: str) -> None:
        """
        Select exam result in dropdown.

        Args:
            result: "قبول" or "رد"
        """
        try:
            self.select_option(self.RESULT_DROPDOWN, result)
        except Exception as e:
            self._save_debug_info(f"Failed to select exam result '{result}': {e}")
            raise AssertionError(f"Could not select exam result '{result}': {e}")

    def click_save_button(self) -> None:
        """Click the save button"""
        try:
            self.click(self.SAVE_BUTTON, timeout=5000)
            # Wait for response
            # Wait for page to load
            import time
            time.sleep(3)
        except Exception as e:
            self._save_debug_info(f"Failed to click save button: {e}")
            raise AssertionError(f"Could not click save button: {e}")

    def is_success_message_displayed(self) -> bool:
        """Check if success message is displayed"""
        try:
            return self.is_visible(self.SUCCESS_MESSAGE, timeout=5000)
        except Exception:
            return False

    def get_success_message(self) -> str:
        """Get success message text"""
        try:
            return self.get_text(self.SUCCESS_MESSAGE)
        except Exception:
            return ""

    def is_error_message_displayed(self) -> bool:
        """Check if error message is displayed"""
        try:
            return self.is_visible(self.ERROR_MESSAGE, timeout=5000)
        except Exception:
            return False

    def get_error_message(self) -> str:
        """Get error message text"""
        try:
            return self.get_text(self.ERROR_MESSAGE)
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
        except Exception:
            return False

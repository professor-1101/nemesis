"""Persian data generator utility for test data generation.

This module provides utilities for generating random Persian/Farsi test data
including names, dates, national codes, addresses, etc.

Clean Architecture:
- Single Responsibility: Only generates test data
- No external dependencies (except standard library)
- Reusable across all test scenarios
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any


class PersianDataGenerator:
    """
    Generate random Persian test data for forms and scenarios.

    This utility class provides methods to generate realistic Persian data
    for testing purposes, including:
    - Persian names (male/female)
    - National codes (with valid checksums)
    - Jalali (Persian) dates
    - Addresses (provinces, cities)
    - ID numbers
    """

    # Persian provinces (30 provinces of Iran)
    PROVINCES: List[str] = [
        "تهران", "اصفهان", "فارس", "خوزستان", "مازندران", "گیلان",
        "آذربایجان شرقی", "آذربایجان غربی", "کرمان", "سیستان و بلوچستان",
        "خراسان رضوی", "خراسان شمالی", "خراسان جنوبی", "البرز",
        "قزوین", "زنجان", "مرکزی", "همدان", "کردستان", "کرمانشاه",
        "لرستان", "ایلام", "چهارمحال و بختیاری", "کهگیلویه و بویراحمد",
        "بوشهر", "هرمزگان", "یزد", "سمنان", "گلستان", "اردبیل"
    ]

    # Persian cities (major cities)
    CITIES: List[str] = [
        "تهران", "اصفهان", "شیراز", "مشهد", "کرج", "اهواز", "رشت", "تبریز",
        "کرمان", "یزد", "قم", "اراک", "زنجان", "همدان", "کرمانشاه", "خرم آباد",
        "سنندج", "بجنورد", "ساری", "گرگان", "اردبیل", "بندرعباس", "زاهدان", "یاسوج"
    ]

    # Persian male first names
    MALE_NAMES: List[str] = [
        "احمد", "محمد", "علی", "حسین", "حسن", "رضا", "مهدی", "امیر",
        "سعید", "حمید", "اکبر", "جعفر", "مرتضی", "ناصر", "فرید",
        "کاظم", "جواد", "مجید", "محمود", "عباس", "غلام", "اسماعیل"
    ]

    # Persian female first names
    FEMALE_NAMES: List[str] = [
        "فاطمه", "زهرا", "مریم", "نازنین", "سمانه", "ملیحه", "زینب",
        "فائزه", "مینا", "نیلوفر", "شیرین", "مژگان", "لیلا", "سپیده",
        "رقیه", "کبری", "سکینه", "معصومه", "پروین", "فرشته"
    ]

    # Persian last names
    LAST_NAMES: List[str] = [
        "احمدی", "رضایی", "کریمی", "حسینی", "محمدی", "علوی", "شیرازی",
        "تهرانی", "اصفهانی", "مشهدی", "کرمانی", "تبریزی", "اهوازی",
        "رشتی", "یزدی", "زنجانی", "همدانی", "کرمانشاهی", "اردبیلی"
    ]

    # Father names (typically male names)
    FATHER_NAMES: List[str] = [
        "حسین", "احمد", "محمد", "علی", "حسن", "رضا", "محمود", "اکبر",
        "جعفر", "ناصر", "فرید", "عباس", "جواد", "کاظم", "غلام", "مجید"
    ]

    # Gender options
    GENDERS: List[str] = ["مرد", "زن"]

    @staticmethod
    def generate_national_code() -> str:
        """
        Generate a valid Iranian national code (کد ملی) with correct checksum.

        National code is 10 digits with the last digit being a checksum.

        Algorithm:
        1. Generate 9 random digits
        2. Calculate sum of (digit * position_weight) where position_weight = 10 - index
        3. Checksum = 11 - (sum % 11), but if < 2 then checksum = sum % 11
        4. Append checksum as 10th digit

        Returns:
            str: Valid 10-digit national code

        Example:
            >>> code = PersianDataGenerator.generate_national_code()
            >>> len(code)
            10
        """
        # Generate first 9 digits
        code_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])

        # Calculate checksum
        total = sum(int(digit) * (10 - i) for i, digit in enumerate(code_digits))
        checksum = total % 11

        # Determine control digit
        control_digit = checksum if checksum < 2 else 11 - checksum

        return code_digits + str(control_digit)

    @staticmethod
    def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
        """
        Convert Gregorian (Western) date to Jalali (Persian/Solar Hijri) date.

        Args:
            gy: Gregorian year
            gm: Gregorian month (1-12)
            gd: Gregorian day (1-31)

        Returns:
            tuple: (jalali_year, jalali_month, jalali_day)

        Example:
            >>> jy, jm, jd = PersianDataGenerator.gregorian_to_jalali(2024, 3, 20)
            >>> jy, jm, jd
            (1402, 12, 30)
        """
        # Days in months for non-leap and leap years
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

        # Calculate base Jalali year
        if gy > 1600:
            jy = 979
            gy -= 1600
        else:
            jy = 0
            gy -= 621

        # Check if leap year
        is_leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
        gy2 = 366 if is_leap else 365

        # Calculate total days
        days = ((gy - 1) * 365 + (gy // 4) - (gy // 100) + (gy // 400) +
                g_d_m[gm - 1] + gd)

        # Adjust for leap year
        if gm > 2 and is_leap:
            days += 1

        # Convert to Jalali
        jy += 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461

        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365

        # Calculate month and day
        if days < 186:
            jm = 1 + days // 31
            jd = 1 + days % 31
        else:
            jm = 7 + (days - 186) // 30
            jd = 1 + (days - 186) % 30

        return jy, jm, jd

    @classmethod
    def generate_birth_date(
        cls,
        min_age: int = 18,
        max_age: int = 65,
        format_type: str = "jalali"
    ) -> str:
        """
        Generate a random birth date in Jalali or Gregorian format.

        Args:
            min_age: Minimum age in years (default: 18)
            max_age: Maximum age in years (default: 65)
            format_type: "jalali" for Persian calendar, "gregorian" for Western (default: "jalali")

        Returns:
            str: Birth date formatted as "YYYY/MM/DD"

        Example:
            >>> date = PersianDataGenerator.generate_birth_date(min_age=20, max_age=50)
            >>> # Returns something like "1380/05/15" (Jalali)
        """
        today = datetime.now()

        # Calculate date range (more than min_age, less than max_age)
        max_date = today - timedelta(days=min_age * 365 + 1)
        min_date = today - timedelta(days=max_age * 365)

        # Generate random date within range
        days_diff = (max_date - min_date).days
        random_days = random.randint(0, days_diff)
        birth_date = min_date + timedelta(days=random_days)

        if format_type == "jalali":
            # Convert to Jalali
            jy, jm, jd = cls.gregorian_to_jalali(
                birth_date.year,
                birth_date.month,
                birth_date.day
            )
            return f"{jy}/{jm:02d}/{jd:02d}"
        else:
            # Return Gregorian
            return birth_date.strftime("%Y/%m/%d")

    @classmethod
    def generate_id_number(cls, min_digits: int = 8, max_digits: int = 10) -> str:
        """
        Generate random ID number (شماره شناسنامه).

        Args:
            min_digits: Minimum number of digits (default: 8)
            max_digits: Maximum number of digits (default: 10)

        Returns:
            str: Random ID number

        Example:
            >>> id_num = PersianDataGenerator.generate_id_number()
            >>> 8 <= len(id_num) <= 10
            True
        """
        num_digits = random.randint(min_digits, max_digits)
        min_val = 10 ** (num_digits - 1)
        max_val = (10 ** num_digits) - 1
        return str(random.randint(min_val, max_val))

    @classmethod
    def generate_male_name(cls) -> str:
        """Generate random Persian male first name."""
        return random.choice(cls.MALE_NAMES)

    @classmethod
    def generate_female_name(cls) -> str:
        """Generate random Persian female first name."""
        return random.choice(cls.FEMALE_NAMES)

    @classmethod
    def generate_first_name(cls, gender: str | None = None) -> str:
        """
        Generate random Persian first name.

        Args:
            gender: "مرد" for male, "زن" for female, None for random (default: None)

        Returns:
            str: Random Persian first name

        Example:
            >>> name = PersianDataGenerator.generate_first_name(gender="مرد")
            >>> name in PersianDataGenerator.MALE_NAMES
            True
        """
        if gender == "مرد":
            return cls.generate_male_name()
        elif gender == "زن":
            return cls.generate_female_name()
        else:
            # Random gender
            return random.choice(cls.MALE_NAMES + cls.FEMALE_NAMES)

    @classmethod
    def generate_last_name(cls) -> str:
        """Generate random Persian last name."""
        return random.choice(cls.LAST_NAMES)

    @classmethod
    def generate_father_name(cls) -> str:
        """Generate random Persian father name."""
        return random.choice(cls.FATHER_NAMES)

    @classmethod
    def generate_gender(cls) -> str:
        """Generate random gender ("مرد" or "زن")."""
        return random.choice(cls.GENDERS)

    @classmethod
    def generate_province(cls) -> str:
        """Generate random Persian province name."""
        return random.choice(cls.PROVINCES)

    @classmethod
    def generate_city(cls) -> str:
        """Generate random Persian city name."""
        return random.choice(cls.CITIES)

    @classmethod
    def generate_personal_data(cls, **overrides) -> Dict[str, Any]:
        """
        Generate complete personal data for form filling.

        This is the main method that generates all required personal information
        for applicant registration forms.

        Args:
            **overrides: Override specific fields (e.g., name="علی", gender="مرد")

        Returns:
            dict: Complete personal data with all required fields

        Example:
            >>> data = PersianDataGenerator.generate_personal_data(name="محمد")
            >>> data['name']
            'محمد'
            >>> len(data['national_code'])
            10
        """
        # Generate gender first (needed for name selection)
        gender = overrides.get('gender', cls.generate_gender())

        # Generate name based on gender
        first_name = overrides.get('name', cls.generate_first_name(gender))
        last_name = overrides.get('family_name', cls.generate_last_name())
        father_name = overrides.get('father_name', cls.generate_father_name())

        # Generate identifiers
        national_code = overrides.get('national_code', cls.generate_national_code())
        id_number = overrides.get('id_number', cls.generate_id_number())
        birth_date = overrides.get('birth_date', cls.generate_birth_date())

        # Generate locations
        province = overrides.get('province', cls.generate_province())
        birth_place_province = overrides.get('birth_place_province', cls.generate_province())
        birth_place = overrides.get('birth_place', cls.generate_city())
        issue_place_province = overrides.get('issue_place_province', cls.generate_province())
        issue_place = overrides.get('issue_place', cls.generate_city())

        # Generate description
        default_description = f"متقاضی {first_name} {last_name} - کد ملی {national_code}"
        description = overrides.get('description', default_description)

        return {
            # Identity
            'name': first_name,
            'family_name': last_name,
            'father_name': father_name,
            'gender': gender,

            # Identifiers
            'national_code': national_code,
            'id_number': id_number,
            'birth_date': birth_date,

            # Locations
            'province': province,
            'birth_place_province': birth_place_province,
            'birth_place': birth_place,
            'issue_place_province': issue_place_province,
            'issue_place': issue_place,

            # Optional fields
            'active': overrides.get('active', True),
            'description': description,
        }

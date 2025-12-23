#!/usr/bin/env python3
"""
Quick test for enhanced action logging in PlaywrightPageAdapter

This script tests the new features:
1. Element details extraction (tag, type, role, aria-label, text)
2. Sensitive data masking
3. Enhanced log formatting
"""

from nemesis.infrastructure.browser.playwright_adapter import PlaywrightBrowserDriver
import time


def test_enhanced_logging():
    """Test enhanced action logging with various element types"""

    print("=" * 80)
    print("Testing Enhanced Action Logging")
    print("=" * 80)

    # Initialize driver with sensitive patterns
    driver = PlaywrightBrowserDriver(
        sensitive_patterns=["password", "secret", "token"],
        mask_character="***MASKED***"
    )

    # Launch browser
    print("\n[1] Launching browser...")
    browser = driver.launch(headless=False)
    page = browser.new_page()

    # Callback to capture logs
    captured_logs = []

    def log_callback(message: str):
        captured_logs.append(message)
        print(f"\n📝 ACTION LOG:\n{message}")
        print("-" * 80)

    # Set action logger
    page.set_action_logger(log_callback)

    try:
        # Test 1: Navigate
        print("\n[2] Testing NAVIGATE action...")
        page.goto("https://www.saucedemo.com")
        time.sleep(1)

        # Test 2: Click on button
        print("\n[3] Testing CLICK action on <input> element...")
        page.click("#user-name")
        time.sleep(0.5)

        # Test 3: Fill with non-sensitive data
        print("\n[4] Testing FILL action with normal data...")
        page.fill("#user-name", "standard_user")
        time.sleep(0.5)

        # Test 4: Fill with sensitive data (should be masked)
        print("\n[5] Testing FILL action with SENSITIVE data (password)...")
        page.fill("#password", "secret_sauce")
        time.sleep(0.5)

        # Test 5: Click login button
        print("\n[6] Testing CLICK action on <input[type=submit]> button...")
        page.click("#login-button")
        time.sleep(2)

        # Test 6: Check visibility
        print("\n[7] Testing CHECK_VISIBILITY action...")
        is_visible = page.is_visible(".inventory_list")
        time.sleep(0.5)

        # Test 7: Get text
        print("\n[8] Testing GET_TEXT action...")
        if is_visible:
            text = page.get_text(".title")
            time.sleep(0.5)

        # Test 8: Screenshot
        print("\n[9] Testing SCREENSHOT action...")
        page.screenshot(path="/tmp/test_screenshot.png")

        # Test 9: JavaScript execution
        print("\n[10] Testing EXECUTE_JAVASCRIPT action...")
        page.evaluate("console.log('Test from Playwright')")

        print("\n" + "=" * 80)
        print(f"✅ Test completed! Captured {len(captured_logs)} action logs")
        print("=" * 80)

        # Verify sensitive data masking
        print("\n[VERIFICATION] Checking sensitive data masking...")
        password_logs = [log for log in captured_logs if "password" in log.lower()]
        for log in password_logs:
            if "***MASKED***" in log:
                print("✅ Password value correctly masked!")
            elif "secret_sauce" in log:
                print("❌ SECURITY ISSUE: Password not masked!")
                return False

        # Verify element details
        print("\n[VERIFICATION] Checking element details...")
        element_detail_logs = [log for log in captured_logs if "Element:" in log]
        if element_detail_logs:
            print(f"✅ Element details captured in {len(element_detail_logs)} logs")
            print("\nExample element detail log:")
            print(element_detail_logs[0])
        else:
            print("❌ No element details found in logs")
            return False

        return True

    finally:
        # Close page
        print("\n[11] Testing CLOSE_PAGE action...")
        page.close()
        time.sleep(0.5)

        # Cleanup
        driver.close()
        print("\n✅ Browser closed successfully")


if __name__ == "__main__":
    try:
        success = test_enhanced_logging()
        if success:
            print("\n" + "=" * 80)
            print("🎉 ALL TESTS PASSED!")
            print("=" * 80)
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

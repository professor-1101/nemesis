@advanced @logging @test_case_id(TC-LOG-001) @attribute(priority:medium)
Feature: Explicit Logging Demonstration
  As a test automation engineer
  I want to add custom log messages to my test reports
  So that I can provide detailed execution information

  Background:
    Given I am on the SauceDemo login page

  @smoke @attribute(component:authentication) @test_case_id(TC-LOG-101)
  Scenario: Login with detailed logging
    # This scenario demonstrates explicit logging at various levels
    When I log message "Starting authentication test" at level "INFO"
    And I log message "Testing with standard_user credentials" at level "DEBUG"
    And I login with username "standard_user" and password "secret_sauce"
    And I log message "Login attempt completed successfully" at level "INFO"
    Then I should see the products page
    And I log message "Products page loaded correctly" at level "INFO"

  @attribute(component:shopping) @test_case_id(TC-LOG-102)
  Scenario: Shopping with debug logging
    # Demonstrates debug-level logging for troubleshooting
    When I log message "Test execution started" at level "INFO"
    And I login with username "standard_user" and password "secret_sauce"
    And I log message "User authenticated successfully" at level "DEBUG"
    And I log message "Navigating to inventory page" at level "DEBUG"
    And I add product "Sauce Labs Backpack" to cart
    And I log message "Product added to cart: Sauce Labs Backpack" at level "INFO"
    And I log message "Cart state updated" at level "DEBUG"
    Then I should see 1 items in the cart
    And I log message "Cart verification passed" at level "INFO"

  @attribute(component:checkout) @test_case_id(TC-LOG-103)
  Scenario: Checkout flow with step-by-step logging
    # Demonstrates logging at each major step
    When I log message "=== Checkout Flow Test Started ===" at level "INFO"
    And I login with username "standard_user" and password "secret_sauce"
    And I log message "Step 1: User logged in" at level "INFO"
    And I add product "Sauce Labs Backpack" to cart
    And I log message "Step 2: Product added to cart" at level "INFO"
    And I go to cart
    And I log message "Step 3: Navigated to cart page" at level "INFO"
    And I proceed to checkout
    And I log message "Step 4: Proceeded to checkout" at level "INFO"
    And I fill checkout information:
      | field      | value     |
      | First Name | Test      |
      | Last Name  | User      |
      | Postal Code| 90210     |
    And I log message "Step 5: Checkout form filled" at level "INFO"
    And I continue to overview
    And I log message "Step 6: Viewing order overview" at level "INFO"
    Then I should see order overview
    And I log message "=== Checkout Flow Test Completed ===" at level "INFO"

  @attribute(component:error_handling) @test_case_id(TC-LOG-104)
  Scenario: Error scenario with warning logs
    # Demonstrates logging for error scenarios
    When I log message "Testing negative scenario" at level "INFO"
    And I log message "Expected behavior: Login should fail" at level "WARN"
    And I login with username "locked_out_user" and password "secret_sauce"
    Then I should see login error message
    And I log message "User account is locked - expected behavior" at level "WARN"
    And I log message "Error handling test completed successfully" at level "INFO"

  @attribute(component:multi_action) @test_case_id(TC-LOG-105)
  Scenario: Complex workflow with trace logging
    # Demonstrates TRACE level for very detailed logging
    When I log message "Complex workflow initiated" at level "INFO"
    And I log message "Attempting authentication" at level "TRACE"
    And I login with username "standard_user" and password "secret_sauce"
    And I log message "Authentication successful, cookies stored" at level "TRACE"
    And I log message "Loading inventory items" at level "TRACE"
    And I add product "Sauce Labs Backpack" to cart
    And I log message "Item 1 added - inventory updated" at level "TRACE"
    And I add product "Sauce Labs Bike Light" to cart
    And I log message "Item 2 added - cart state synchronized" at level "TRACE"
    And I go to cart
    And I log message "Cart page rendered with 2 items" at level "TRACE"
    Then I should see 2 items in the cart
    And I log message "Cart verification successful - workflow complete" at level "INFO"

@advanced @metadata @test_case_id(TC-META-001) @attribute(priority:high)
Feature: Metadata API Demonstration
  As a test automation engineer
  I want to enrich my test reports with custom metadata
  So that I can provide better context and traceability

  Background:
    Given I am on the SauceDemo login page

  @smoke @attribute(component:authentication) @test_case_id(TC-META-101)
  Scenario: Login with metadata enrichment
    # This scenario demonstrates runtime metadata enrichment
    When I add metadata "test_environment" with value "staging"
    And I add metadata "browser_version" with value "Chrome 120.0.6099.109"
    And I add metadata "test_user" with value "standard_user"
    And I login with username "standard_user" and password "secret_sauce"
    Then I should see the products page
    And I add metadata "login_duration_ms" with value "250"
    And I add metadata "test_result" with value "successful_login"

  @attribute(component:shopping) @test_case_id(TC-META-102)
  Scenario: Shopping cart with performance metadata
    # Demonstrates metadata for performance tracking
    When I login with username "standard_user" and password "secret_sauce"
    And I add metadata "page_load_time_ms" with value "320"
    And I add product "Sauce Labs Backpack" to cart
    And I add metadata "add_to_cart_duration_ms" with value "150"
    And I add product "Sauce Labs Bike Light" to cart
    And I add metadata "cart_items_count" with value "2"
    Then I should see 2 items in the cart
    And I add metadata "test_data_id" with value "CART-DATA-12345"

  @attribute(component:checkout) @attribute(payment:credit_card) @test_case_id(TC-META-103)
  Scenario: Checkout with transaction metadata
    # Demonstrates metadata for transaction tracking
    When I login with username "standard_user" and password "secret_sauce"
    And I add product "Sauce Labs Backpack" to cart
    And I go to cart
    And I proceed to checkout
    And I add metadata "transaction_id" with value "TXN-20251217-001"
    And I add metadata "payment_method" with value "credit_card"
    And I fill checkout information:
      | field      | value     |
      | First Name | John      |
      | Last Name  | Doe       |
      | Postal Code| 12345     |
    And I add metadata "billing_country" with value "USA"
    And I continue to overview
    And I add metadata "order_total" with value "$29.99"
    Then I should see order overview
    And I add metadata "test_status" with value "checkout_complete"

  @attribute(component:error_handling) @test_case_id(TC-META-104)
  Scenario: Login failure with error metadata
    # Demonstrates metadata for error tracking
    When I add metadata "test_scenario" with value "negative_test"
    And I add metadata "expected_result" with value "login_failure"
    And I login with username "invalid_user" and password "wrong_password"
    Then I should see login error message
    And I add metadata "error_type" with value "authentication_failed"
    And I add metadata "error_message" with value "Username and password do not match"

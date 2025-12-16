@shopping @cart
Feature: Shopping Cart Management
  As a logged-in user
  I want to manage my shopping cart
  So that I can prepare items for checkout

  Background:
    Given I am logged in as "standard_user"
    And I am on the inventory page

  @positive
  Scenario: Add product to cart successfully
    When I add "Sauce Labs Backpack" to cart
    Then the cart badge should show "1"
    When I click on the cart icon
    Then I should see "Sauce Labs Backpack" in the cart
    And the price should be "$29.99"

  @negative
  Scenario: View empty cart
    When I click on the cart icon
    Then the cart should be empty
    And I should see cart headers
    And the "Continue Shopping" button should be visible
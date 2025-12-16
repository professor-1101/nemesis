@checkout @critical
Feature: Checkout Process
  As a user with items in cart
  I want to complete the checkout process
  So that I can purchase products

  Background:
    Given I am logged in as "standard_user"
    And I have added "Sauce Labs Backpack" to cart
    And I am on the cart page
    And I click the "Checkout" button

  @positive @e2e
  Scenario: Complete checkout with valid information
    When I enter first name "John"
    And I enter last name "Doe"
    And I enter postal code "12345"
    And I click the "Continue" button
    Then I should see the checkout overview page
    And I should see payment information
    And I should see shipping information
    When I click the "Finish" button
    Then I should see "Thank you for your order!" message
    And I should see the Pony Express image

  @negative @validation
  Scenario: Checkout without first name
    When I leave first name empty
    And I enter last name "Doe"
    And I enter postal code "12345"
    And I click the "Continue" button
    Then I should see error "Error: First Name is required"
    And I should remain on checkout information page
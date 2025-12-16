@authentication @critical
Feature: User Authentication
  As a user of SauceDemo
  I want to login to the application
  So that I can access the inventory

  Background:
    Given I am on the SauceDemo login page

  @positive @smoke
  Scenario: Successful login with standard user
    When I enter username "standard_user"
    And I enter password "secret_sauce"
    And I click the login button
    Then I should be redirected to the inventory page
    And I should see "Products" header
    And the shopping cart icon should be visible

  @negative
  Scenario: Login attempt with locked out user
    When I enter username "locked_out_user"
    And I enter password "secret_sauce"
    And I click the login button
    Then I should see error message "Epic sadface: Sorry, this user has been locked out."
    And I should remain on the login page
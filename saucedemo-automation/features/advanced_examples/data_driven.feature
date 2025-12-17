@advanced @data_driven @test_case_id(TC-DDT-001) @attribute(priority:high)
Feature: Data-Driven Testing Demonstration
  As a test automation engineer
  I want to run the same test with multiple data sets
  So that I can achieve better test coverage with minimal code

  Background:
    Given I am on the SauceDemo login page

  @smoke @attribute(component:authentication) @test_case_id(TC-DDT-101)
  Scenario Outline: Login with multiple valid users
    # Data-driven test for multiple valid user accounts
    When I add metadata "user_type" with value "<user_type>"
    And I login with username "<username>" and password "<password>"
    Then I should see the products page
    And I add metadata "login_result" with value "success"

    Examples: Valid Users
      | username                | password     | user_type           |
      | standard_user           | secret_sauce | standard            |
      | problem_user            | secret_sauce | problem_simulator   |
      | performance_glitch_user | secret_sauce | performance_test    |

  @negative @attribute(component:authentication) @test_case_id(TC-DDT-102)
  Scenario Outline: Login with invalid credentials
    # Data-driven negative testing
    When I add metadata "test_type" with value "negative"
    And I add metadata "username_tested" with value "<username>"
    And I login with username "<username>" and password "<password>"
    Then I should see login error message
    And I add metadata "error_scenario" with value "<scenario>"

    Examples: Invalid Credentials
      | username        | password        | scenario            |
      | invalid_user    | secret_sauce    | invalid_username    |
      | standard_user   | wrong_password  | invalid_password    |
      | locked_out_user | secret_sauce    | locked_account      |
      |                 | secret_sauce    | empty_username      |
      | standard_user   |                 | empty_password      |

  @attribute(component:shopping) @test_case_id(TC-DDT-103)
  Scenario Outline: Add multiple products to cart
    # Data-driven product selection
    When I login with username "standard_user" and password "secret_sauce"
    And I add metadata "product_name" with value "<product_name>"
    And I add metadata "product_price" with value "<price>"
    And I add product "<product_name>" to cart
    Then I should see 1 items in the cart
    And I log message "Added <product_name> priced at <price>" at level "INFO"

    Examples: Product Catalog
      | product_name                      | price   |
      | Sauce Labs Backpack               | $29.99  |
      | Sauce Labs Bike Light             | $9.99   |
      | Sauce Labs Bolt T-Shirt           | $15.99  |
      | Sauce Labs Fleece Jacket          | $49.99  |
      | Sauce Labs Onesie                 | $7.99   |
      | Test.allTheThings() T-Shirt (Red) | $15.99  |

  @attribute(component:checkout) @test_case_id(TC-DDT-104)
  Scenario Outline: Checkout with different user information
    # Data-driven checkout form validation
    When I login with username "standard_user" and password "secret_sauce"
    And I add product "Sauce Labs Backpack" to cart
    And I go to cart
    And I proceed to checkout
    And I add metadata "customer_name" with value "<first_name> <last_name>"
    And I add metadata "postal_code" with value "<postal_code>"
    And I fill checkout information:
      | field       | value         |
      | First Name  | <first_name>  |
      | Last Name   | <last_name>   |
      | Postal Code | <postal_code> |
    And I continue to overview
    Then I should see order overview
    And I log message "Checkout completed for <first_name> <last_name>" at level "INFO"

    Examples: Customer Information
      | first_name | last_name | postal_code |
      | John       | Doe       | 12345       |
      | Jane       | Smith     | 90210       |
      | Bob        | Johnson   | 10001       |
      | Alice      | Williams  | 60601       |
      | Charlie    | Brown     | 02134       |

  @attribute(component:sorting) @test_case_id(TC-DDT-105)
  Scenario Outline: Product sorting verification
    # Data-driven sorting validation
    When I login with username "standard_user" and password "secret_sauce"
    And I add metadata "sort_option" with value "<sort_option>"
    And I log message "Testing sort: <sort_option>" at level "INFO"
    And I sort products by "<sort_option>"
    Then products should be sorted by "<sort_option>"
    And I add metadata "sort_result" with value "verified"

    Examples: Sorting Options
      | sort_option           |
      | Name (A to Z)         |
      | Name (Z to A)         |
      | Price (low to high)   |
      | Price (high to low)   |

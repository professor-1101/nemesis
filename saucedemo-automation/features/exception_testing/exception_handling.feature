Feature: Exception Handling and Stack Trace Testing
  As a test automation engineer
  I want to test exception handling and stack trace logging
  So that I can verify Stack Traces appear correctly in ReportPortal

  Scenario: Test Exception Handling
    Given I want to test exception handling
    When I trigger a test exception
    Then I should see the exception in ReportPortal
    And I should see the stack trace in ReportPortal

  Scenario: Test Timeout Exception
    Given I want to test exception handling
    When I trigger a timeout exception
    Then I should see the exception in ReportPortal
    And I should see the stack trace in ReportPortal

  Scenario: Test Connection Exception
    Given I want to test exception handling
    When I trigger a connection exception
    Then I should see the exception in ReportPortal
    And I should see the stack trace in ReportPortal

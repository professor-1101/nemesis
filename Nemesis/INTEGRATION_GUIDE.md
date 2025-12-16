# Nemesis Integration Guide - Clean Architecture

این راهنما نحوه استفاده از معماری جدید Nemesis را با مثال‌های کامل توضیح می‌دهد.

---

## 📋 فهرست

1. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
2. [Dependency Injection Setup](#dependency-injection-setup)
3. [استفاده از Domain Model](#استفاده-از-domain-model)
4. [اجرای تست با Use Cases](#اجرای-تست-با-use-cases)
5. [مثال کامل BDD](#مثال-کامل-bdd)
6. [کانفیگوریشن](#کانفیگوریشن)
7. [Migration از کد قدیمی](#migration-از-کد-قدیمی)

---

## 1️⃣ نصب و راه‌اندازی

### نصب Nemesis

```bash
pip install nemesis-automation
```

### ساختار پروژه

```
my-test-project/
├── features/
│   ├── environment.py      # Behave hooks با Nemesis
│   ├── login.feature
│   └── steps/
│       └── login_steps.py
├── pages/
│   └── login_page.py
├── conf/
│   ├── playwright.yaml
│   ├── logging.yaml
│   └── reporting.yaml
└── requirements.txt
```

---

## 2️⃣ Dependency Injection Setup

### Composition Root (`features/environment.py`)

```python
"""
Behave environment file with Clean Architecture Dependency Injection

This is the Composition Root where we wire up all dependencies.
"""

from pathlib import Path
from typing import Any

# Domain Layer
from nemesis.domain import (
    Execution, Scenario, Step,
    ExecutionId, ScenarioStatus,
)

# Application Layer
from nemesis.application import (
    ExecutionCoordinator,
    ReportingCoordinator,
    ScenarioCoordinator,
)

# Infrastructure Layer (Adapters)
from nemesis.infrastructure import (
    PlaywrightBrowserDriver,
    JSONReporter,
    ConsoleReporter,
    SigNozShipper,
    LocalFileShipper,
)


def before_all(context: Any) -> None:
    """
    Setup dependencies (Dependency Injection)

    This is the Composition Root - where we wire everything together.
    """

    # 1. Create Browser Driver (adapter)
    browser_driver = PlaywrightBrowserDriver()
    browser_driver.set_browser_type("chromium")
    context.browser_driver = browser_driver

    # 2. Create Reporters (adapters)
    reporters = [
        ConsoleReporter(),  # Beautiful CLI output
        JSONReporter(output_dir=Path("reports")),  # JSON reports
    ]
    context.reporters = reporters

    # 3. Create Log Shippers (adapters)
    log_shippers = [
        LocalFileShipper(log_file_path=Path("logs/test.log")),
        # SigNozShipper(
        #     endpoint="http://localhost:4317/v1/logs",
        #     service_name="my-test-project",
        # ),
    ]
    context.log_shippers = log_shippers

    # 4. Create Collectors (empty for now)
    context.collectors = []

    # 5. Create Application Services (Coordinators)
    context.execution_coordinator = ExecutionCoordinator(
        reporters=reporters,
        output_dir=Path("reports"),
    )

    context.reporting_coordinator = ReportingCoordinator(reporters=reporters)

    context.scenario_coordinator = ScenarioCoordinator(
        browser_driver=browser_driver,
        reporters=reporters,
        collectors=context.collectors,
    )

    # 6. Start Execution
    execution_id = ExecutionId.generate()
    context.execution = context.execution_coordinator.start_execution(
        execution_id=execution_id,
        metadata={
            "environment": "dev",
            "browser": "chromium",
        }
    )


def after_all(context: Any) -> None:
    """Cleanup and generate final reports"""

    # End execution and generate reports
    execution = context.execution_coordinator.end_execution()

    # Close browser
    context.browser_driver.close()

    # Close log shippers
    for shipper in context.log_shippers:
        shipper.close()

    # Print summary
    print(f"\n{'='*50}")
    print(f"Execution Summary:")
    print(f"  Total Scenarios: {execution.get_total_scenarios_count()}")
    print(f"  Passed: {execution.get_passed_scenarios_count()}")
    print(f"  Failed: {execution.get_failed_scenarios_count()}")
    print(f"  Duration: {execution.get_duration()}")
    print(f"{'='*50}\n")


def before_scenario(context: Any, scenario: Any) -> None:
    """Setup scenario"""

    # Create Scenario entity (Domain Model)
    context.scenario = Scenario.create(
        name=scenario.name,
        feature_name=scenario.feature.name,
        tags=[tag for tag in scenario.tags],
    )

    # Add steps to scenario
    for behave_step in scenario.steps:
        step = Step.create(
            name=behave_step.name,
            keyword=behave_step.keyword,
        )
        context.scenario.add_step(step)

    # Launch browser
    browser = context.browser_driver.launch(headless=False)
    page = browser.new_page()

    # Store in context
    context.browser = browser
    context.page = page

    # Report scenario start
    context.reporting_coordinator.start_scenario(context.scenario)


def after_scenario(context: Any, scenario: Any) -> None:
    """Cleanup scenario"""

    # Complete scenario (status calculated from steps)
    context.scenario.complete()

    # Report scenario end
    context.reporting_coordinator.end_scenario(context.scenario)

    # Add scenario to execution
    context.execution_coordinator.add_scenario(context.scenario)

    # Close browser
    if hasattr(context, 'browser'):
        context.browser.close()


def before_step(context: Any, step: Any) -> None:
    """Setup step"""

    # Find corresponding domain step
    for domain_step in context.scenario.steps:
        if domain_step.name == step.name:
            context.current_step = domain_step
            break

    # Start step
    context.current_step.start()

    # Report step start
    context.reporting_coordinator.start_step(context.current_step)


def after_step(context: Any, step: Any) -> None:
    """Cleanup step"""

    # Update step status based on Behave result
    if step.status.name == "passed":
        context.current_step.complete_successfully()
    elif step.status.name == "failed":
        error_msg = str(step.exception) if step.exception else "Step failed"
        context.current_step.fail(error_msg)
    elif step.status.name == "skipped":
        context.current_step.skip()

    # Report step end
    context.reporting_coordinator.end_step(context.current_step)
```

---

## 3️⃣ استفاده از Domain Model

### مثال 1: ایجاد Execution

```python
from nemesis.domain import Execution, ExecutionId

# Generate execution ID
execution_id = ExecutionId.generate()  # exec_20250416_143052

# Create execution
execution = Execution.create(execution_id)

# Add metadata
execution.add_metadata("environment", "staging")
execution.add_metadata("browser", "chromium")

# Add scenarios (shown below)
execution.add_scenario(scenario1)
execution.add_scenario(scenario2)

# Complete execution
execution.complete()

# Get statistics
print(f"Total: {execution.get_total_scenarios_count()}")
print(f"Passed: {execution.get_passed_scenarios_count()}")
print(f"Failed: {execution.get_failed_scenarios_count()}")
print(f"Duration: {execution.get_duration()}")
```

### مثال 2: ایجاد Scenario

```python
from nemesis.domain import Scenario, Step, ScenarioStatus

# Create scenario
scenario = Scenario.create(
    name="Login with valid credentials",
    feature_name="Authentication",
    tags=["@smoke", "@critical"],
)

# Start scenario
scenario.start()  # PENDING → RUNNING

# Add steps
step1 = Step.create(name="Enter username", keyword="When")
step1.start()
step1.complete_successfully()
scenario.add_step(step1)

step2 = Step.create(name="Enter password", keyword="And")
step2.start()
step2.complete_successfully()
scenario.add_step(step2)

step3 = Step.create(name="Click login button", keyword="And")
step3.start()
step3.complete_successfully()
scenario.add_step(step3)

# Complete scenario (status calculated from steps)
scenario.complete()  # All passed → PASSED

# Check results
print(f"Status: {scenario.status}")  # ScenarioStatus.PASSED
print(f"Successful: {scenario.is_successful()}")  # True
print(f"Duration: {scenario.get_duration()}")  # e.g., "5.3s"
print(f"Passed steps: {scenario.get_passed_steps_count()}")  # 3
```

### مثال 3: Value Objects

```python
from nemesis.domain import ExecutionId, ScenarioStatus, Duration

# ExecutionId - Type-safe, validated
execution_id = ExecutionId.generate()
print(execution_id)  # exec_20250416_143052

# Extract timestamp
timestamp = execution_id.extract_timestamp()
print(timestamp)  # 2025-04-16 14:30:52+00:00

# ScenarioStatus - Type-safe enum
status = ScenarioStatus.PASSED

if status.is_terminal():
    print("Scenario completed")

if status.is_successful():
    print("Scenario passed!")

# Duration - Self-formatting
duration = Duration.from_seconds(125.4)
print(duration.format_short())  # "125.4s"
print(duration.format_human())  # "2m 5s"
print(str(duration))  # "2m 5s"
```

---

## 4️⃣ اجرای تست با Use Cases

### Direct Use Case Usage (Advanced)

```python
from nemesis.application.use_cases import ExecuteTestScenarioUseCase
from nemesis.domain import Scenario, Step

# Setup dependencies
browser_driver = PlaywrightBrowserDriver()
reporters = [ConsoleReporter(), JSONReporter(Path("reports"))]
collectors = []

# Create use case
use_case = ExecuteTestScenarioUseCase(
    browser_driver=browser_driver,
    reporters=reporters,
    collectors=collectors,
)

# Create scenario
scenario = Scenario.create(
    name="Login test",
    feature_name="Authentication",
)

# Define step executor
def execute_step(step: Step):
    """Execute step logic"""
    if "username" in step.name:
        page.fill("#username", "user@example.com")
    elif "password" in step.name:
        page.fill("#password", "password123")
    elif "login" in step.name:
        page.click("#login-button")

# Execute scenario
scenario = use_case.execute(scenario, execute_step)

# Check results
print(f"Scenario status: {scenario.status}")
```

---

## 5️⃣ مثال کامل BDD

### Feature File (`features/login.feature`)

```gherkin
@authentication
Feature: User Authentication
  As a user
  I want to login to the application
  So that I can access my account

  @smoke @critical
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter username "user@example.com"
    And I enter password "secret123"
    And I click the login button
    Then I should see the dashboard
    And I should see my username "user@example.com"
```

### Step Definitions (`features/steps/login_steps.py`)

```python
from behave import given, when, then
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


@given('I am on the login page')
def step_navigate_to_login(context):
    """Navigate to login page"""
    # context.page is provided by Nemesis (via before_scenario)
    login_page = LoginPage(context.page)
    login_page.open()
    context.login_page = login_page


@when('I enter username "{username}"')
def step_enter_username(context, username):
    """Enter username"""
    context.login_page.enter_username(username)


@when('I enter password "{password}"')
def step_enter_password(context, password):
    """Enter password"""
    context.login_page.enter_password(password)


@when('I click the login button')
def step_click_login(context):
    """Click login button"""
    context.login_page.click_login()
    context.dashboard_page = DashboardPage(context.page)


@then('I should see the dashboard')
def step_verify_dashboard(context):
    """Verify dashboard is displayed"""
    assert context.dashboard_page.is_displayed(), "Dashboard not displayed"


@then('I should see my username "{username}"')
def step_verify_username(context, username):
    """Verify username is displayed"""
    displayed_username = context.dashboard_page.get_username()
    assert displayed_username == username, f"Expected {username}, got {displayed_username}"
```

### Page Object (`pages/login_page.py`)

```python
from pathlib import Path
from nemesis.domain.ports import IPage


class LoginPage:
    """
    Page Object using IPage interface

    Clean Architecture:
    - Depends on IPage interface, not Playwright
    - Can work with any browser automation (Playwright, Selenium)
    """

    def __init__(self, page: IPage, base_url: str = "https://example.com"):
        """
        Initialize page object

        Args:
            page: Browser page (IPage interface, not Playwright!)
            base_url: Base URL of application
        """
        self.page = page
        self.base_url = base_url

    def open(self) -> None:
        """Navigate to login page"""
        self.page.goto(f"{self.base_url}/login")

    def enter_username(self, username: str) -> None:
        """Enter username"""
        self.page.fill("#username", username)

    def enter_password(self, password: str) -> None:
        """Enter password"""
        self.page.fill("#password", password)

    def click_login(self) -> None:
        """Click login button"""
        self.page.click("#login-button")

    def get_error_message(self) -> str:
        """Get error message"""
        return self.page.get_text(".error-message")
```

---

## 6️⃣ کانفیگوریشن

### Logging Config (`conf/logging.yaml`)

```yaml
level: INFO

shipping:
  signoz:
    enabled: true
    service_name: my-test-project
    endpoint: http://localhost:4317/v1/logs
    batch_size: 100
    retry_attempts: 3

  local:
    enabled: true
    log_file: logs/test.log
```

### Reporting Config (`conf/reporting.yaml`)

```yaml
reporters:
  console:
    enabled: true

  json:
    enabled: true
    output_dir: reports
    pretty_print: true
```

---

## 7️⃣ Migration از کد قدیمی

### قبل (کد قدیمی)

```python
# ❌ BAD: Direct Playwright dependency
from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):  # Coupled to Playwright!
        self.page = page

# ❌ BAD: Primitive obsession
execution_id: str = "exec_20250416_143052"
status: str = "PASSED"  # Typo-prone

# ❌ BAD: Anemic model
@dataclass
class ScenarioData:
    name: str
    status: str  # Just data, no behavior
```

### بعد (کد جدید)

```python
# ✅ GOOD: Interface dependency
from nemesis.domain.ports import IPage

class LoginPage:
    def __init__(self, page: IPage):  # Interface, not framework!
        self.page = page

# ✅ GOOD: Value Objects
from nemesis.domain import ExecutionId, ScenarioStatus

execution_id = ExecutionId.generate()  # Type-safe, validated
status = ScenarioStatus.PASSED  # Enum, no typos

# ✅ GOOD: Rich domain model
from nemesis.domain import Scenario

scenario = Scenario.create(name="Login", feature_name="Auth")
scenario.start()  # Business logic
scenario.complete()  # Status auto-calculated
```

---

## 🎯 خلاصه مزایا

### Framework Independence
```python
# Can swap Playwright for Selenium WITHOUT changing test code
browser_driver = SeleniumBrowserDriver()  # Instead of Playwright
# Test code remains unchanged!
```

### Type Safety
```python
# ❌ Before: Runtime errors
status = "PASSSED"  # Typo!

# ✅ After: Compile-time safety
status = ScenarioStatus.PASSED  # Cannot typo enum
```

### Testability
```python
# ✅ Can test domain logic WITHOUT infrastructure
from nemesis.domain import Scenario

def test_scenario_status_calculation():
    scenario = Scenario.create("Test", "Feature")
    scenario.start()

    # Add failed step
    step = Step.create("Failed step", "When")
    step.start()
    step.fail("Error")
    scenario.add_step(step)

    # Complete scenario
    scenario.complete()

    # Assert status
    assert scenario.is_failed()  # No browser needed!
```

---

## 📚 منابع بیشتر

- [README.md](README_NEW.md) - معماری کامل
- [ARCHITECTURAL_ANALYSIS.md](ARCHITECTURAL_ANALYSIS.md) - تحلیل معماری
- [Domain Model API Reference](docs/domain_model.md)

---

**یادداشت**: این معماری بر اساس Clean Architecture و DDD است. هدف framework independence و maintainability است، نه complexity! 🎯

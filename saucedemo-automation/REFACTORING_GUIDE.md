# SauceDemo Automation - Clean Architecture Refactoring Guide

This document explains the refactoring of the SauceDemo test automation project to use Nemesis Framework's new Clean Architecture implementation.

## Table of Contents
- [What Changed](#what-changed)
- [Architecture Overview](#architecture-overview)
- [Key Improvements](#key-improvements)
- [Migration Guide](#migration-guide)
- [Running Tests](#running-tests)
- [Examples](#examples)

## What Changed

### Before: Direct Framework Coupling
```python
# OLD: Direct Playwright imports
from playwright.sync_api import Page
from nemesis.core.exceptions import ElementNotFoundError
from nemesis.core.logging import Logger
from nemesis.environment import before_all, after_all

class BasePage:
    def __init__(self, page: Page, config: Any):  # Coupled to Playwright
        self.page = page
```

### After: Clean Architecture with Abstractions
```python
# NEW: Framework-independent abstractions
from nemesis.domain.ports import IPage
from nemesis.infrastructure.browser import PlaywrightBrowserDriver
from nemesis.infrastructure.reporting import ConsoleReporter, JSONReporter

class BasePage:
    def __init__(self, page: IPage, config: dict):  # Interface, not Playwright
        self.page = page
```

## Architecture Overview

### Dependency Flow (Clean Architecture)

```
┌─────────────────────────────────────────┐
│         Test Project (BDD)              │
│                                         │
│  ┌─────────────┐    ┌───────────────┐ │
│  │  Features   │───▶│ Step Defs     │ │
│  │  (.feature) │    │ (login_steps) │ │
│  └─────────────┘    └───────────────┘ │
│                            │           │
│                            ▼           │
│  ┌──────────────────────────────────┐ │
│  │      Page Objects                │ │
│  │  (LoginPage, InventoryPage)      │ │
│  │                                  │ │
│  │  Uses IPage interface            │ │
│  └──────────────────────────────────┘ │
│                            │           │
└────────────────────────────┼───────────┘
                             │
                             ▼
┌─────────────────────────────────────────┐
│    Nemesis Framework (Clean Arch)       │
│                                         │
│  ┌──────────────────────────────────┐ │
│  │  Domain Layer                    │ │
│  │                                  │ │
│  │  - IPage (interface)             │ │
│  │  - IBrowserDriver (interface)    │ │
│  │  - IReporter (interface)         │ │
│  │  - Entities (Scenario, Step)     │ │
│  │  - Value Objects (Status, Id)    │ │
│  └──────────────────────────────────┘ │
│                  ▲                     │
│                  │                     │
│  ┌──────────────┴───────────────────┐ │
│  │  Application Layer               │ │
│  │                                  │ │
│  │  - ExecutionCoordinator          │ │
│  │  - ScenarioCoordinator           │ │
│  │  - Use Cases                     │ │
│  └──────────────────────────────────┘ │
│                  ▲                     │
│                  │                     │
│  ┌──────────────┴───────────────────┐ │
│  │  Infrastructure Layer            │ │
│  │                                  │ │
│  │  - PlaywrightBrowserDriver       │ │
│  │  - ConsoleReporter (Cypress-like)│ │
│  │  - JSONReporter                  │ │
│  └──────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Layers Explained

#### 1. Domain Layer (Core Business Logic)
- **Entities**: `Execution`, `Scenario`, `Step` with rich behavior
- **Value Objects**: `ExecutionId`, `ScenarioStatus`, `StepStatus`, `Duration`
- **Ports (Interfaces)**: `IPage`, `IBrowserDriver`, `IReporter`

#### 2. Application Layer (Orchestration)
- **Coordinators**: `ExecutionCoordinator`, `ScenarioCoordinator`
- **Use Cases**: `ExecuteTestScenarioUseCase`, `GenerateExecutionReportUseCase`

#### 3. Infrastructure Layer (Technical Implementation)
- **Browser Adapters**: `PlaywrightBrowserDriver`, `PlaywrightPageAdapter`
- **Reporters**: `ConsoleReporter`, `JSONReporter`
- **Log Shippers**: `SigNozShipper`, `LocalFileShipper`

## Key Improvements

### 1. Framework Independence
**Before:** Directly coupled to Playwright
```python
from playwright.sync_api import Page

def my_test(page: Page):  # Can only use Playwright
    page.goto("https://example.com")
```

**After:** Uses abstraction (IPage)
```python
from nemesis.domain.ports import IPage

def my_test(page: IPage):  # Can use Playwright, Selenium, or any driver
    page.goto("https://example.com")
```

### 2. Dependency Injection (Composition Root)
**Before:** Hardcoded dependencies scattered everywhere

**After:** Single place for wiring up dependencies
```python
# environment.py - Composition Root
class DependencyContainer:
    def __init__(self, config: dict):
        # Infrastructure: Choose implementations here
        self.browser_driver = PlaywrightBrowserDriver(browser_type="chromium")

        self.reporters = [
            ConsoleReporter(),  # Cypress-like CLI output
            JSONReporter(output_dir=self.output_dir),
        ]

        # Application: Coordinators with injected dependencies
        self.execution_coordinator = ExecutionCoordinator(
            reporters=self.reporters,
            output_dir=self.output_dir
        )
```

### 3. Rich Domain Model
**Before:** Anemic data structures
```python
scenario = {"name": "Login", "status": "PASSED"}  # Just data
```

**After:** Rich entities with behavior
```python
scenario = Scenario.create(name="Login", feature_name="Authentication")
scenario.start()  # Business logic encapsulated
scenario.add_step(step)
scenario.complete()  # Calculates status from steps
```

### 4. Type Safety with Value Objects
**Before:** Primitive obsession
```python
status = "PASSED"  # Can have typos: "PASSD", "passed"
```

**After:** Type-safe enums
```python
status = ScenarioStatus.PASSED  # Compile-time safety
```

### 5. Clean Reporting
**Before:** HTML generation in framework (Allure integration)

**After:** Framework generates JSON only
- **ConsoleReporter**: Cypress-like CLI output with colors
- **JSONReporter**: Structured JSON for custom visualization
- Test projects choose their own HTML rendering

## Migration Guide

### Step 1: Update environment.py

```python
from nemesis.domain.entities import Execution, Scenario, Step
from nemesis.infrastructure.browser import PlaywrightBrowserDriver
from nemesis.infrastructure.reporting import ConsoleReporter, JSONReporter

class DependencyContainer:
    def __init__(self, config: dict):
        self.browser_driver = PlaywrightBrowserDriver(browser_type="chromium")
        self.reporters = [ConsoleReporter(), JSONReporter(output_dir=Path("./reports"))]

def before_all(context):
    config = {
        "browser_type": "chromium",
        "headless": False,
        "base_url": "https://www.saucedemo.com"
    }
    context.container = DependencyContainer(config)
    context.execution = context.container.start_execution()
```

### Step 2: Update BasePage

```python
from nemesis.domain.ports import IPage

class BasePage:
    def __init__(self, page: IPage, config: dict):  # Use IPage interface
        self.page = page
        self.config = config

    def navigate_to(self, path: str = "") -> None:
        url = f"{self.base_url}{path}"
        self.page.goto(url)  # Uses IPage.goto()
```

### Step 3: Update Page Objects

```python
from nemesis.domain.ports import IPage
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page: IPage, config: dict):  # IPage interface
        super().__init__(page, config)

    def login(self, username: str, password: str) -> None:
        self.fill("#user-name", username)  # Uses IPage methods
        self.fill("#password", password)
        self.click("#login-button")
```

### Step 4: Step Definitions (No Change Needed!)

```python
from behave import given, when, then
from pages.login_page import LoginPage

@given("I am on the SauceDemo login page")
def step_navigate_to_login(context):
    # context.page is now IPage implementation
    context.login_page = LoginPage(context.page, context.config)
    context.login_page.open()
```

## Running Tests

### Installation

```bash
# Install Nemesis framework (refactored version)
cd ../Nemesis
pip install -e .
playwright install chromium

# Install test project dependencies
cd ../saucedemo-automation
pip install -r requirements.txt
```

### Execute Tests

```bash
# Run all tests with Behave directly
behave features/

# Run with specific browser
behave features/ -D browser=chromium

# Run in headless mode
behave features/ -D headless=true

# Run with custom output directory
behave features/ -D output_dir=./reports/$(date +%Y%m%d)

# Run specific feature
behave features/authentication/login.feature

# Run with tags
behave features/ --tags=@smoke
```

### Output

**Console Output (Cypress-like):**
```
NEMESIS Test Automation Framework
─────────────────────────────────────

  User Authentication
    ✓ Successful login with standard user (1.2s)
    ✗ Login attempt with locked out user (0.8s)
      Epic sadface: Sorry, this user has been locked out.

─────────────────────────────────────
  2 passing (2.0s)
  0 failing
─────────────────────────────────────
```

**JSON Report:**
```json
{
  "execution_id": "exec_20251216_143045",
  "start_time": "2025-12-16T14:30:45Z",
  "scenarios": [
    {
      "name": "Successful login with standard user",
      "feature_name": "User Authentication",
      "status": "PASSED",
      "duration": "1.2s",
      "steps": [...]
    }
  ]
}
```

## Examples

### Example 1: Simple Login Test

```python
# features/steps/login_steps.py
from behave import given, when, then
from pages.login_page import LoginPage

@given("I am on the SauceDemo login page")
def step_impl(context):
    context.login_page = LoginPage(context.page, context.config)
    context.login_page.open()

@when('I login with username "{username}" and password "{password}"')
def step_impl(context, username, password):
    context.login_page.login(username, password)

@then("I should see the inventory page")
def step_impl(context):
    context.login_page.assert_url_contains("/inventory.html")
```

### Example 2: Custom Page Object

```python
# pages/my_custom_page.py
from nemesis.domain.ports import IPage
from pages.base_page import BasePage

class MyCustomPage(BasePage):
    """
    Custom page using Clean Architecture
    """

    SEARCH_INPUT = "#search"
    SUBMIT_BUTTON = "#submit"

    def __init__(self, page: IPage, config: dict):
        super().__init__(page, config)

    def search(self, query: str) -> None:
        """Business logic: Perform search"""
        self.fill(self.SEARCH_INPUT, query)
        self.click(self.SUBMIT_BUTTON)
```

### Example 3: Advanced Browser Configuration

```python
# environment.py
def before_all(context):
    config = {
        "browser_type": "chromium",
        "headless": True,
        "base_url": "https://www.saucedemo.com",
        "output_dir": "./reports",
    }

    # Create container with custom config
    context.container = DependencyContainer(config)

    # Launch browser with custom options
    context.container.launch_browser(
        headless=config["headless"],
        args=["--start-maximized"]
    )
```

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Framework Coupling** | Tightly coupled to Playwright | Framework-independent via IPage |
| **Dependency Management** | Scattered hardcoded deps | Centralized Composition Root |
| **Domain Model** | Anemic data structures | Rich entities with behavior |
| **Type Safety** | String primitives | Type-safe Value Objects |
| **Reporting** | Framework generates HTML | Framework generates JSON, projects choose visualization |
| **Testability** | Hard to test (needs Playwright) | Easy to mock interfaces |
| **Architecture** | No clear layers | Clean Architecture (Domain → Application → Infrastructure) |

## Next Steps

1. **Run tests** to verify everything works
2. **Review reports** in `./reports` directory
3. **Customize** reporters if needed (create your own IReporter implementation)
4. **Extend** domain model for your specific needs
5. **Add** more page objects following the IPage pattern

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'nemesis.domain'"

**Solution:** Install the refactored Nemesis framework
```bash
cd ../Nemesis
pip install -e .
```

### Issue: "AttributeError: 'PlaywrightPageAdapter' object has no attribute 'playwright_page'"

**Solution:** This shouldn't happen in the refactored version. The adapter exposes `playwright_page` property for advanced usage.

### Issue: Tests fail with "Element not found"

**Solution:** The new architecture uses the same Playwright under the hood, so selectors should work the same. Check if selectors are correct.

## Resources

- **Nemesis Framework Documentation**: `../Nemesis/README_NEW.md`
- **Integration Guide**: `../Nemesis/INTEGRATION_GUIDE.md`
- **Architecture Analysis**: `../Nemesis/ARCHITECTURAL_ANALYSIS.md`
- **Implementation Report**: `../FINAL_IMPLEMENTATION_REPORT.md`

---

**Happy Testing with Clean Architecture! 🎉**

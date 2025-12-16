# Nemesis Test Automation Framework

**A Clean Architecture BDD Test Automation Framework for Python**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Domain Model](#domain-model)
- [Dependency Injection](#dependency-injection)
- [Logging & Observability](#logging--observability)
- [Reporting](#reporting)
- [CLI Usage](#cli-usage)
- [Design Decisions](#design-decisions)
- [Contributing](#contributing)

---

## 🎯 Overview

Nemesis is a **production-grade** test automation framework built on **Clean Architecture** and **Domain-Driven Design** principles. It provides a framework-independent core with pluggable adapters for browser automation, reporting, and observability.

### Why Nemesis?

- **Framework Independence**: Swap Playwright for Selenium without touching business logic
- **Clean Architecture**: Clear separation between domain, application, and infrastructure layers
- **Type Safety**: Rich domain model with Value Objects eliminates primitive obsession
- **Testable**: Pure domain logic testable without infrastructure dependencies
- **Observable**: Built-in SigNoz integration for distributed tracing and logging
- **Professional**: Production-ready code following SOLID principles

---

## 🏗️ Architecture

Nemesis follows **Hexagonal Architecture** (Ports & Adapters) combined with **Domain-Driven Design**:

```
┌────────────────────────────────────────────────────────────────┐
│                        CLI Layer                               │
│                  (User Interface)                              │
└────────────────┬───────────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────────┐
│                   Application Layer                            │
│         (Use Cases, Services, Coordinators)                    │
└─────┬──────────────────────────────────────────┬───────────────┘
      │                                          │
┌─────▼──────────────────────────────────────────▼───────────────┐
│                      Domain Layer                              │
│   • Entities: Execution, Scenario, Step                       │
│   • Value Objects: ExecutionId, ScenarioStatus, Duration      │
│   • Ports (Interfaces): IBrowserDriver, IReporter, ICollector │
│   • Business Logic & Invariants                               │
└────────────────────────────────────────────────────────────────┘
                 ▲                          ▲
                 │                          │
┌────────────────┴──────────┐  ┌────────────┴───────────────────┐
│  Infrastructure Layer     │  │  Infrastructure Layer          │
│  • PlaywrightAdapter      │  │  • ReportPortalReporter        │
│  • SeleniumAdapter        │  │  • JSONReporter                │
│  • ConsoleCollector       │  │  • SigNozShipper               │
│  • PerformanceCollector   │  │  • LocalFileShipper            │
└───────────────────────────┘  └────────────────────────────────┘
```

### Dependency Rule

> **Dependencies point inward**: Infrastructure → Application → Domain

- **Domain Layer**: No external dependencies. Pure business logic.
- **Application Layer**: Depends only on Domain. Orchestrates use cases.
- **Infrastructure Layer**: Depends on Domain & Application. Implements ports (interfaces).
- **CLI Layer**: Depends on all layers. Composition root.

---

## ✨ Key Features

### 1. Rich Domain Model

Replace primitive strings with type-safe Value Objects:

```python
# ❌ Before: Primitive Obsession
execution_id: str = "exec_20250416_123456"
status: str = "PASSED"  # Typo-prone, no validation

# ✅ After: Rich Domain Model
execution_id = ExecutionId.generate()  # Type-safe, validated
status = ScenarioStatus.PASSED  # Enum, type-safe
```

### 2. Dependency Inversion

Swap frameworks without changing business logic:

```python
# Domain defines interface (Port)
class IBrowserDriver(ABC):
    @abstractmethod
    def launch(self, headless: bool) -> IBrowser: ...

# Infrastructure implements adapter
class PlaywrightBrowserDriver(IBrowserDriver):
    def launch(self, headless: bool) -> IBrowser:
        # Playwright-specific implementation
        ...

# Easy to add Selenium adapter
class SeleniumBrowserDriver(IBrowserDriver):
    def launch(self, headless: bool) -> IBrowser:
        # Selenium-specific implementation
        ...
```

### 3. Business Logic in Entities

Domain entities contain behavior, not just data:

```python
# Rich Scenario entity with business logic
scenario = Scenario.create(name="Login Test", feature_name="Authentication")
scenario.start()

# Add steps
step = Step.create(name="Enter username", keyword="When")
step.start()
step.complete_successfully()
scenario.add_step(step)

# Business rule: Status derived from steps
scenario.complete()  # Automatically calculates PASSED/FAILED from steps
assert scenario.is_successful()
```

### 4. No HTML Reporting

**Design Decision**: Framework generates **JSON only**. Test projects decide how to visualize.

```python
# Nemesis generates structured JSON
reporter = JSONReporter(output_dir)
reporter.generate_report(execution)  # → execution_report.json

# Test project can use any visualization:
# - Allure (external tool)
# - Custom HTML generator
# - CI/CD dashboard integration
```

---

## 📦 Installation

```bash
pip install nemesis-automation
```

### Development Installation

```bash
git clone https://github.com/yourorg/nemesis.git
cd nemesis
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### 1. Initialize Project

```bash
nemesis init my-test-project
cd my-test-project
```

### 2. Create Feature File

```gherkin
# features/login.feature
Feature: User Authentication
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
```

### 3. Implement Step Definitions

```python
# features/steps/login_steps.py
from behave import given, when, then
from pages.login_page import LoginPage

@given("I am on the login page")
def step_navigate_to_login(context):
    # context.page provided by Nemesis
    login_page = LoginPage(context.page)
    login_page.open()

@when("I enter valid credentials")
def step_enter_credentials(context):
    login_page = context.login_page
    login_page.login("user@example.com", "password")

@then("I should see the dashboard")
def step_verify_dashboard(context):
    assert context.page.is_visible("h1:has-text('Dashboard')")
```

### 4. Run Tests

```bash
nemesis run --tags @smoke --headless
```

---

## ⚙️ Configuration

Nemesis uses YAML configuration files for all settings.

### Browser Configuration (`conf/playwright.yaml`)

```yaml
browser:
  type: chromium  # chromium, firefox, webkit
  headless: false
  slow_mo: 0
  args:
    - --start-maximized
    - --disable-web-security

viewport:
  width: 1920
  height: 1080

context:
  record_video:
    enabled: true
    mode: retain-on-failure  # always, retain-on-failure, off

timeouts:
  default: 30000
  navigation: 30000
```

### Logging Configuration (`conf/logging.yaml`)

```yaml
level: INFO
format: structured  # structured, json, simple

console:
  enabled: true
  level: INFO
  format: rich  # rich console output

file:
  enabled: true
  level: DEBUG
  path: logs/nemesis.log
  rotation:
    enabled: true
    max_size: 10MB
    backup_count: 5

shipping:
  signoz:
    enabled: true
    service_name: my-test-project
    endpoint: http://signoz:4317/v1/logs
    batch_size: 100
    retry_attempts: 3

  local:
    enabled: true
    log_directory: ./logs
```

### Reporting Configuration (`conf/reporting.yaml`)

```yaml
mode: all  # json, reportportal, all

json:
  enabled: true
  output_dir: reports
  pretty_print: true

reportportal:
  enabled: true
  send_artifacts: true
  step_level_reporting: true
  max_attachment_size: 10485760  # 10MB
```

---

## 🧬 Domain Model

### Value Objects

Immutable, self-validating objects representing domain concepts:

#### ExecutionId

```python
from nemesis.domain import ExecutionId

# Generate new ID
execution_id = ExecutionId.generate()  # exec_20250416_143052

# From string (with validation)
execution_id = ExecutionId.from_string("exec_20250416_143052")

# Extract timestamp
timestamp = execution_id.extract_timestamp()  # datetime object
```

#### ScenarioStatus

```python
from nemesis.domain import ScenarioStatus

status = ScenarioStatus.PASSED  # Type-safe enum

# Business logic methods
if status.is_terminal():  # Check if final status
    print("Scenario completed")

if status.is_successful():
    print("Scenario passed")

# From string (case-insensitive)
status = ScenarioStatus.from_string("passed")  # ScenarioStatus.PASSED
```

#### Duration

```python
from nemesis.domain import Duration

# Create duration
duration = Duration.from_seconds(125.4)

# Formatting
duration.format_short()  # "125.4s"
duration.format_human()  # "2m 5s"

# Arithmetic
total = duration1 + duration2

# Comparison
if duration1 > duration2:
    print("Slower")
```

### Entities

Objects with identity and lifecycle:

#### Step

```python
from nemesis.domain import Step, StepStatus

# Create step
step = Step.create(name="Enter username", keyword="When")

# Lifecycle
step.start()  # PENDING → RUNNING
step.complete_successfully()  # RUNNING → PASSED

# Or fail
step.fail("Element not found")  # RUNNING → FAILED

# Query state
duration = step.get_duration()
is_done = step.is_completed()
```

#### Scenario

```python
from nemesis.domain import Scenario

# Create scenario
scenario = Scenario.create(
    name="Login with valid credentials",
    feature_name="Authentication",
    tags=["@smoke", "@critical"]
)

# Lifecycle
scenario.start()
scenario.add_step(step1)
scenario.add_step(step2)
scenario.complete()  # Status calculated from steps

# Query
passed_count = scenario.get_passed_steps_count()
failed_count = scenario.get_failed_steps_count()
duration = scenario.get_duration()
```

#### Execution

```python
from nemesis.domain import Execution

# Create execution
execution = Execution.create()

# Add scenarios
execution.add_scenario(scenario1)
execution.add_scenario(scenario2)
execution.complete()

# Statistics
total = execution.get_total_scenarios_count()
passed = execution.get_passed_scenarios_count()
failed = execution.get_failed_scenarios_count()
duration = execution.get_duration()

# Query
is_successful = execution.is_successful()
has_failures = execution.has_failures()
```

---

## 🔌 Dependency Injection

Nemesis uses **Protocol-based dependency injection** for flexibility.

### Ports (Interfaces)

Defined in `nemesis.domain.ports`:

```python
from nemesis.domain.ports import IBrowserDriver, IReporter, ICollector

# Browser driver port
class IBrowserDriver(ABC):
    @abstractmethod
    def launch(self, headless: bool, args: list[str]) -> IBrowser: ...

# Reporter port
class IReporter(ABC):
    @abstractmethod
    def start_scenario(self, scenario: Scenario) -> None: ...
    @abstractmethod
    def end_scenario(self, scenario: Scenario) -> None: ...

# Collector port
class ICollector(ABC):
    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def get_collected_data(self) -> list[dict]: ...
```

### Adapters (Implementations)

Implemented in `nemesis.infrastructure`:

```python
from nemesis.domain.ports import IBrowserDriver
from playwright.sync_api import sync_playwright

class PlaywrightBrowserDriver(IBrowserDriver):
    """Playwright adapter for browser automation"""

    def launch(self, headless: bool, args: list[str]) -> IBrowser:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=headless, args=args)
        return PlaywrightBrowserAdapter(browser)
```

### Composition Root

Dependency injection happens at application startup:

```python
# features/environment.py
from nemesis.infrastructure.browser import PlaywrightBrowserDriver
from nemesis.infrastructure.reporting import JSONReporter, ReportPortalReporter

def before_all(context):
    # Inject dependencies
    browser_driver = PlaywrightBrowserDriver()
    reporters = [
        JSONReporter(output_dir="reports"),
        ReportPortalReporter(config),
    ]

    # Initialize application services
    context.browser_driver = browser_driver
    context.reporters = reporters
```

---

## 📊 Logging & Observability

Nemesis includes **structured logging** with **SigNoz integration** for distributed tracing.

### Log Structure

All logs follow a standard format:

```json
{
  "timestamp": 1703123456.789,
  "level": "INFO",
  "message": "Scenario started: Login with valid credentials",
  "correlation_id": "uuid-1234-5678",
  "execution_id": "exec_20250416_143052",
  "context": {
    "scenario_id": "scenario_abc123",
    "feature": "Authentication",
    "tags": ["@smoke"]
  },
  "service_name": "my-test-project",
  "module": "scenario_coordinator"
}
```

### Context Propagation

Correlation IDs automatically propagate through all components:

```python
from nemesis.core.logging import Logger

logger = Logger.get_instance()

# Correlation ID automatically included
logger.info("Starting scenario", scenario_id="scenario_123", feature="Login")
```

### SigNoz Integration

Ship logs to SigNoz observability platform:

```yaml
# conf/logging.yaml
shipping:
  signoz:
    enabled: true
    service_name: my-test-project
    endpoint: http://signoz:4317/v1/logs
    batch_size: 100
    retry_attempts: 3
```

Benefits:
- **Distributed Tracing**: Track requests across services
- **Correlation**: Link logs by correlation_id
- **Visualization**: Real-time dashboards
- **Alerting**: Set up alerts on failures

---

## 📈 Reporting

Nemesis **generates JSON reports only**. No HTML generation in the framework.

### JSON Report Structure

```json
{
  "execution_id": "exec_20250416_143052",
  "start_time": "2025-04-16T14:30:52Z",
  "end_time": "2025-04-16T14:35:23Z",
  "duration": 271.5,
  "total_scenarios": 10,
  "passed_scenarios": 9,
  "failed_scenarios": 1,
  "total_steps": 45,
  "passed_steps": 43,
  "failed_steps": 2,
  "is_successful": false,
  "scenarios": [...]
}
```

### Using External Report Generators

Test projects can visualize JSON using:

#### Allure (External Tool)

```bash
# Install Allure
npm install -g allure-commandline

# Generate converter (test project)
python convert_to_allure.py reports/execution_report.json

# Generate HTML
allure generate allure-results -o allure-report
allure open allure-report
```

#### Custom HTML Template

```python
# test-project/generate_html.py
from jinja2 import Template
import json

with open("reports/execution_report.json") as f:
    data = json.load(f)

template = Template(open("templates/report.html").read())
html = template.render(execution=data)

with open("reports/report.html", "w") as f:
    f.write(html)
```

### ReportPortal Integration

Real-time test management platform:

```yaml
# conf/reportportal.yaml
endpoint: https://reportportal.example.com
project: my-project
api_key: ${RP_API_KEY}
launch_name: Regression Tests
launch_description: Automated regression suite
```

---

## 🖥️ CLI Usage

Nemesis provides a powerful CLI inspired by Cypress.

### Run Tests

```bash
# Run all tests
nemesis run

# Run with tags
nemesis run --tags @smoke
nemesis run --tags @critical --tags @regression

# Run specific feature
nemesis run --feature features/login.feature

# Headless mode
nemesis run --headless

# Parallel execution
nemesis run --parallel 4

# Specific environment
nemesis run --env staging

# Debug mode
nemesis run --debug --verbose
```

### Initialize Project

```bash
nemesis init my-project
```

Creates project structure:

```
my-project/
├── conf/
│   ├── playwright.yaml
│   ├── logging.yaml
│   ├── reporting.yaml
│   └── reportportal.yaml
├── features/
│   ├── environment.py
│   └── steps/
├── pages/
│   └── base_page.py
└── requirements.txt
```

### Validate Configuration

```bash
nemesis validate
```

Checks:
- ✓ Configuration files syntax
- ✓ Required fields present
- ✓ Environment variables set
- ✓ Dependencies installed

### List Executions

```bash
nemesis list
```

Shows recent test executions:

```
Recent Executions:
┌────────────────────────┬──────────┬────────┬────────┬──────────┐
│ Execution ID           │ Date     │ Passed │ Failed │ Duration │
├────────────────────────┼──────────┼────────┼────────┼──────────┤
│ exec_20250416_143052   │ 16/04/25 │ 9      │ 1      │ 4m 31s   │
│ exec_20250416_102315   │ 16/04/25 │ 10     │ 0      │ 3m 45s   │
└────────────────────────┴──────────┴────────┴────────┴──────────┘
```

---

## 🎨 Design Decisions

### 1. Why No HTML Reporting in Framework?

**Decision**: Nemesis generates JSON only. HTML generation is test project responsibility.

**Rationale**:
- **Single Responsibility**: Framework handles test execution, not visualization
- **Flexibility**: Test projects choose their own reporting tools
- **Separation of Concerns**: Framework independent of UI presentation
- **Maintainability**: Less framework code to maintain

**How to Generate HTML**:
- Use Allure (external tool)
- Use custom Jinja2 templates
- Integrate with CI/CD dashboards

### 2. Why Dependency Inversion?

**Decision**: Core depends on interfaces (ports), not concrete implementations.

**Rationale**:
- **Framework Independence**: Can swap Playwright for Selenium
- **Testability**: Mock interfaces for unit tests
- **Extensibility**: Add new adapters without changing core
- **SOLID Compliance**: Dependency Inversion Principle

### 3. Why Rich Domain Model?

**Decision**: Entities contain behavior, not just data.

**Rationale**:
- **Business Logic Encapsulation**: Logic lives with data
- **Type Safety**: Value Objects prevent invalid states
- **Testability**: Domain logic testable without infrastructure
- **DDD Compliance**: Ubiquitous language in code

### 4. Why SigNoz for Logging?

**Decision**: Built-in SigNoz integration for observability.

**Rationale**:
- **Distributed Tracing**: Track test execution across services
- **Correlation**: Link logs with correlation IDs
- **Real-time**: Live dashboard during test runs
- **Open Source**: No vendor lock-in

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourorg/nemesis.git
cd nemesis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
flake8 src/
mypy src/
black src/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Clean Architecture** by Robert C. Martin
- **Domain-Driven Design** by Eric Evans
- **Hexagonal Architecture** by Alistair Cockburn
- Inspired by **Cypress** CLI UX

---

**Built with ❤️ using Clean Architecture and DDD**

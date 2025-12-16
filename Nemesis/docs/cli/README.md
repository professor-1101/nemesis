# Nemesis CLI Documentation

**Beautiful, Cypress-like CLI for BDD Test Automation**

---

## 📖 Table of Contents

- [Quick Start](#quick-start)
- [Commands](#commands)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Best Practices](#best-practices)

---

## 🚀 Quick Start

### Installation

```bash
pip install nemesis-test-framework
```

### Initialize Project

```bash
nemesis init
```

This creates:
- `nemesis.config.yml` - Main configuration file
- `features/` - BDD feature files directory
- `features/steps/` - Step definitions directory
- `features/environment.py` - Behave hooks

### Run Tests

```bash
# Run all tests
nemesis run

# Run with tags
nemesis run --tags @smoke

# Run specific feature
nemesis run --feature features/login.feature

# Run in headed mode
nemesis run --headed
```

### View Results

```bash
# List recent executions
nemesis list

# Open latest report
nemesis open
```

---

## 📋 Commands

### `nemesis run`

Execute test scenarios with beautiful, real-time feedback.

**Syntax:**
```bash
nemesis run [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--tags` | `-t` | Run scenarios with specific tags | All |
| `--feature` | `-f` | Run specific feature file | All |
| `--env` | `-e` | Environment (dev, staging, prod) | `dev` |
| `--headless` | - | Run browser in headless mode | `False` |
| `--headed` | - | Run browser in headed mode | `True` |
| `--parallel` | `-p` | Number of parallel workers | `1` |
| `--browser` | `-b` | Browser (chromium, firefox, webkit) | `chromium` |
| `--report` | `-r` | Report mode (local, reportportal, all) | `all` |
| `--open` | `-o` | Open report after execution | `False` |
| `--debug` | - | Enable debug logging | `False` |
| `--verbose` | `-v` | Enable verbose output | `False` |
| `--dry-run` | - | Validate scenarios without execution | `False` |

**Examples:**

```bash
# Basic usage
nemesis run

# Smoke tests only
nemesis run --tags @smoke

# Multiple tags (OR)
nemesis run --tags @smoke --tags @critical

# Tag expressions (AND)
nemesis run --tags "@smoke and @critical"

# Tag exclusion
nemesis run --tags "@smoke and not @wip"

# Specific feature
nemesis run --feature features/login.feature

# Production environment, headless
nemesis run --env prod --headless

# Parallel execution
nemesis run --parallel 4

# Firefox browser
nemesis run --browser firefox

# Auto-open report
nemesis run --open

# Debug mode
nemesis run --debug --verbose
```

**Output Example:**

```
┌────────────────────────────────────────┐
│         Running Tests                  │
│                                        │
│ Execution: exec_20251216_120000       │
│ Progress: 2/5 scenarios (40%)          │
│ Elapsed: 15s                           │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ✓ Login Feature: User can login       │
│                                        │
│   ✓ Given I am on login page    0.5s  │
│   ✓ When I enter credentials    0.8s  │
│   → ● Then I should see dashboard      │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│            Test Results                 │
├────────────────────────────────────────┤
│ ✓ Passing      15                      │
│ ✗ Failing       2                      │
│ ○ Skipped       1                      │
│                                        │
│ Steps Passed   45                      │
│ Steps Failed    3                      │
└────────────────────────────────────────┘
```

---

### `nemesis init`

Initialize a new Nemesis project with configuration and directory structure.

**Syntax:**
```bash
nemesis init [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--template` | Project template (basic, advanced) | `basic` |
| `--browser` | Default browser | `chromium` |
| `--force` | Overwrite existing configuration | `False` |

**Examples:**

```bash
# Basic initialization
nemesis init

# Advanced template
nemesis init --template advanced

# Force reinitialize
nemesis init --force
```

**Created Structure:**

```
project/
├── nemesis.config.yml          # Main configuration
├── features/                   # BDD features
│   ├── login.feature
│   ├── steps/
│   │   └── login_steps.py
│   └── environment.py          # Behave hooks
├── reports/                    # Test reports (auto-created)
└── .gitignore
```

---

### `nemesis list`

List recent test executions with results.

**Syntax:**
```bash
nemesis list [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--limit` | Number of executions to show | `10` |
| `--env` | Filter by environment | All |

**Examples:**

```bash
# List recent executions
nemesis list

# Last 5 executions
nemesis list --limit 5

# Production executions only
nemesis list --env prod
```

**Output Example:**

```
Recent Executions

┌────────────────────────┬──────────┬─────────┬─────────┬──────────┐
│ Execution ID           │ Passed   │ Failed  │ Duration │ Time     │
├────────────────────────┼──────────┼─────────┼──────────┼──────────┤
│ exec_20251216_120000   │ 15       │ 0       │ 23.5s    │ 2h ago   │
│ exec_20251216_110000   │ 12       │ 3       │ 45.2s    │ 3h ago   │
│ exec_20251216_100000   │ 15       │ 0       │ 22.1s    │ 4h ago   │
└────────────────────────┴──────────┴─────────┴──────────┴──────────┘
```

---

### `nemesis open`

Open the latest test report in browser.

**Syntax:**
```bash
nemesis open [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--execution-id` | Specific execution to open | Latest |

**Examples:**

```bash
# Open latest report
nemesis open

# Open specific execution
nemesis open --execution-id exec_20251216_120000
```

---

### `nemesis clean`

Clean old test reports and artifacts.

**Syntax:**
```bash
nemesis clean [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--days` | Keep reports newer than N days | `7` |
| `--dry-run` | Preview without deleting | `False` |

**Examples:**

```bash
# Clean reports older than 7 days
nemesis clean

# Keep last 3 days only
nemesis clean --days 3

# Preview what would be deleted
nemesis clean --dry-run
```

---

### `nemesis validate`

Validate feature files and step definitions without execution.

**Syntax:**
```bash
nemesis validate [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--feature` | Validate specific feature | All |

**Examples:**

```bash
# Validate all features
nemesis validate

# Validate specific feature
nemesis validate --feature features/login.feature
```

**Output Example:**

```
Validating Features

✓ features/login.feature
  ✓ Scenario: User can login
    ✓ Given I am on login page
    ✓ When I enter valid credentials
    ✓ Then I should see dashboard

✗ features/checkout.feature
  ✓ Scenario: Add item to cart
    ✓ Given I am logged in
    ✗ When I add item to cart
      Step definition not found

Validation Summary:
  ✓ 12 scenarios valid
  ✗ 1 scenario with issues
```

---

## ⚙️ Configuration

### Configuration File

`nemesis.config.yml` - Main configuration file

```yaml
# Project Configuration
project:
  name: "My Test Project"
  version: "1.0.0"

# Browser Configuration
browser:
  type: "chromium"  # chromium, firefox, webkit
  headless: false
  viewport:
    width: 1280
    height: 720
  timeout: 30000  # milliseconds

# Environments
environments:
  dev:
    base_url: "https://dev.example.com"
  staging:
    base_url: "https://staging.example.com"
  prod:
    base_url: "https://example.com"

# Reporting
reporting:
  local:
    enabled: true
    output_dir: "reports"
  reportportal:
    enabled: false
    endpoint: "http://reportportal.example.com"
    project: "my_project"
    api_token: "${RP_TOKEN}"  # Use environment variable

# Execution
execution:
  parallel: 1
  retry_failed: false
  screenshot_on_failure: true
  video: true
  trace: true

# Observability
observability:
  tracing:
    enabled: true
    endpoint: "http://signoz.example.com:4317"
    service_name: "nemesis-tests"
  logging:
    level: "INFO"
    format: "json"
```

### Environment Variables

```bash
# ReportPortal
export RP_TOKEN="your-api-token"
export RP_ENDPOINT="http://reportportal.example.com"

# Observability
export OTEL_EXPORTER_OTLP_ENDPOINT="http://signoz.example.com:4317"

# Browser
export NEMESIS_BROWSER="chromium"
export NEMESIS_HEADLESS="true"

# Environment
export NEMESIS_ENV="prod"
```

---

## 🏗️ Architecture

### Clean Architecture

Nemesis follows Clean Architecture principles:

```
┌─────────────────────────────────────┐
│         CLI Layer                    │
│  (Commands, UI, Progress)           │
└──────────────┬──────────────────────┘
               │ Uses
               ▼
┌─────────────────────────────────────┐
│      Application Layer               │
│  (Use Cases, Coordinators)          │
└──────────────┬──────────────────────┘
               │ Uses
               ▼
┌─────────────────────────────────────┐
│         Domain Layer                 │
│  (Entities, Value Objects, Ports)   │
└──────────────┬──────────────────────┘
               │ Implemented by
               ▼
┌─────────────────────────────────────┐
│     Infrastructure Layer             │
│  (Playwright, Reporters, Loggers)   │
└─────────────────────────────────────┘
```

**Benefits:**
- **Testable**: Domain logic tested independently
- **Flexible**: Swap browsers/reporters without changing core logic
- **Maintainable**: Clear separation of concerns
- **Scalable**: Easy to add new features

---

## ✨ Best Practices

### 1. Tag Organization

```gherkin
@smoke @critical
Feature: Login

  @smoke @positive
  Scenario: User can login with valid credentials
    ...

  @smoke @negative
  Scenario: User cannot login with invalid password
    ...

  @regression @edge-case
  Scenario: User account locked after 5 failed attempts
    ...
```

**Run tags:**
```bash
# Smoke tests
nemesis run --tags @smoke

# Critical smoke tests
nemesis run --tags "@smoke and @critical"

# All except WIP
nemesis run --tags "not @wip"
```

### 2. Environment Strategy

**Use environment-specific configs:**
```yaml
environments:
  dev:
    base_url: "https://dev.example.com"
    timeout: 60000  # More lenient for dev
  prod:
    base_url: "https://example.com"
    timeout: 30000  # Strict for prod
```

**Run per environment:**
```bash
# Development (default)
nemesis run

# Production
nemesis run --env prod --headless
```

### 3. Parallel Execution

```bash
# Use parallel workers for faster execution
nemesis run --parallel 4

# For large test suites
nemesis run --parallel 8 --tags @regression
```

**Note:** Ensure tests are independent!

### 4. CI/CD Integration

**GitLab CI example:**
```yaml
test:
  stage: test
  script:
    - nemesis run --env staging --headless --parallel 4
  artifacts:
    when: always
    paths:
      - reports/
    reports:
      junit: reports/*/junit.xml
```

**GitHub Actions example:**
```yaml
- name: Run Tests
  run: |
    nemesis run --env staging --headless --parallel 4
- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: test-report
    path: reports/
```

### 5. Debugging

```bash
# Enable debug output
nemesis run --debug --verbose

# Run in headed mode
nemesis run --headed

# Dry run (validate only)
nemesis run --dry-run

# Single scenario
nemesis run --tags @debug
```

---

## 🎯 Comparison with Cypress

| Feature | Cypress | Nemesis |
|---------|---------|---------|
| **Language** | JavaScript | Python |
| **Test Style** | Mocha/Chai | BDD (Gherkin) |
| **Browser** | Chromium, Firefox, Edge | Chromium, Firefox, WebKit |
| **Parallel** | ✅ Paid | ✅ Free |
| **Real-time UI** | ✅ | ✅ |
| **Video Recording** | ✅ | ✅ |
| **Screenshots** | ✅ | ✅ |
| **Trace Viewer** | ✅ | ✅ |
| **ReportPortal** | ❌ | ✅ |
| **Distributed Tracing** | ❌ | ✅ |
| **Clean Architecture** | ❌ | ✅ |

---

## 📚 Additional Resources

- [Feature Writing Guide](../features/README.md)
- [Step Definitions Guide](../steps/README.md)
- [Architecture Guide](../architecture/README.md)
- [API Reference](../api/README.md)
- [Contributing Guide](../../CONTRIBUTING.md)

---

## 🐛 Troubleshooting

### Tests not found
```bash
# Verify feature files exist
ls features/*.feature

# Validate features
nemesis validate
```

### Browser launch failed
```bash
# Install browser drivers
playwright install chromium

# Check browser type
nemesis run --browser chromium --debug
```

### Report not generated
```bash
# Check output directory
ls -la reports/

# Check permissions
chmod -R 755 reports/

# Enable debug logging
nemesis run --debug
```

---

## 💡 Tips & Tricks

1. **Quick smoke test run:**
   ```bash
   nemesis run --tags @smoke --headless
   ```

2. **Watch mode (auto-rerun on changes):**
   ```bash
   # Coming soon!
   nemesis run --watch
   ```

3. **Generate test report only:**
   ```bash
   nemesis report --execution-id exec_20251216_120000
   ```

4. **Export results to JSON:**
   ```bash
   # Reports are automatically saved as JSON
   cat reports/exec_*/execution.json | jq .
   ```

5. **Integration with VS Code:**
   - Install Cucumber extension
   - Use `.feature` files with syntax highlighting
   - Jump to step definitions with Ctrl+Click

---

**Made with ❤️ using Clean Architecture & DDD principles**

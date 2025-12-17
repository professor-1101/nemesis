# SauceDemo Test Automation

A comprehensive BDD test automation project for SauceDemo e-commerce application using Nemesis framework, Behave, and Playwright.

## 🎯 Project Overview

This project demonstrates end-to-end testing of the SauceDemo application with:
- **BDD Scenarios**: Gherkin-based test cases
- **Page Object Model**: Maintainable page interactions
- **Multi-Environment**: Dev, Staging, Production configurations
- **Rich Reporting**: HTML, ReportPortal integration
- **Artifact Collection**: Screenshots, videos, traces, network logs

## 📁 Project Structure

```
saucedemo-automation/
├── config/                    # Configuration files
│   ├── behave.ini            # Behave settings
│   ├── playwright.yaml       # Browser configuration
│   ├── reporting.yaml        # Report settings
│   ├── reportportal.yaml     # ReportPortal config
│   └── environments/         # Environment-specific configs
│       ├── dev.yaml          # Development environment
│       ├── staging.yaml      # Staging environment
│       └── prod.yaml         # Production environment
├── features/                 # BDD test scenarios
│   ├── environment.py        # Test lifecycle hooks
│   ├── authentication/       # Login scenarios
│   ├── shopping/            # Cart management
│   └── checkout/            # Checkout process
├── pages/                   # Page Object Model
│   ├── base_page.py         # Base page class
│   ├── login_page.py        # Login page
│   ├── inventory_page.py    # Product listing
│   ├── cart_page.py         # Shopping cart
│   └── checkout_page.py     # Checkout process
├── reports/                 # Test execution reports
├── logs/                    # Execution logs
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Nemesis framework installed
- Playwright browsers installed

### Installation

1. **Install Nemesis Framework**
   ```bash
   cd ../nemesis
   pip install -e .
   playwright install chromium
   ```

2. **Setup Project**
   ```bash
   cd ../saucedemo-automation
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Set environment variables as needed
   ```

### Running Tests

#### Basic Commands
```bash
# Run all tests
nemesis run

# Run with specific tags
nemesis run --tags @smoke
nemesis run --tags @critical
nemesis run --tags @positive
nemesis run --tags @negative

# Run specific feature
nemesis run --feature authentication/login.feature

# Run with environment
nemesis run --env dev
nemesis run --env staging
nemesis run --env prod
```

#### Advanced Options
```bash
# Parallel execution
nemesis run --parallel 4

# Headless mode
nemesis run --headless

# Debug mode
nemesis run --debug --no-headless

# Dry run (validation only)
nemesis run --dry-run

# Report modes
nemesis run -r local           # Local HTML only
nemesis run -r reportportal    # ReportPortal only
nemesis run -r all            # All reporters
```

## 🧪 Test Scenarios

### Authentication Tests
- ✅ **Successful Login**: Standard user login flow
- ❌ **Locked User**: Error handling for locked accounts
- ❌ **Invalid Credentials**: Error handling for wrong credentials

### Shopping Cart Tests
- ✅ **Add Product**: Add items to cart
- ✅ **View Cart**: Navigate to cart page
- ❌ **Empty Cart**: Handle empty cart state

### Checkout Tests
- ✅ **Complete Checkout**: Full checkout process
- ❌ **Validation Errors**: Form validation testing
- ✅ **Order Confirmation**: Success flow verification

## 📊 Reports & Artifacts

### Local Reports
```bash
# View HTML report
open reports/2025-10-18_14-30-45_abc123/report.html

# View Playwright trace
playwright show-trace reports/2025-10-18_14-30-45_abc123/traces/scenario.zip

```

### Report Structure
```
reports/2025-10-18_14-30-45_abc123/
├── report.html              # Main HTML report
├── screenshots/             # Step screenshots
├── videos/                  # Scenario videos
├── traces/                  # Playwright traces
├── network/                 # HAR files & metrics
├── performance/             # Performance metrics
└── console/                 # Browser console logs
```

## 🎯 ReportPortal Features Demonstrated

This project showcases all ReportPortal capabilities available in the Nemesis framework:

### 1. Automatic Features

#### Test Hierarchy
- **Launch** → **Suite** (Feature) → **Scenario** (Test) → **Step**
- Proper BDD structure maintained in ReportPortal
- Configurable step layouts (SCENARIO/STEP/NESTED)

#### Automatic Attachments
- **Screenshots**: Captured on failures
- **Videos**: Full scenario recordings
- **Traces**: Playwright execution traces
- **HAR Files**: Network traffic logs
- **Console Logs**: Browser console messages
- **Performance Metrics**: Navigation timing, web vitals

#### Exception Handling
- Full stack traces logged to ReportPortal
- Automatic exception capture with context
- Fallback mechanisms for robust reporting

### 2. Manual Features (Advanced Examples)

#### Custom Metadata Enrichment
```gherkin
# features/advanced_examples/metadata_demo.feature
Scenario: Login with metadata enrichment
  When I add metadata "test_environment" with value "staging"
  And I add metadata "browser_version" with value "Chrome 120"
  And I add metadata "test_user" with value "standard_user"
  And I login with username "standard_user" and password "secret_sauce"
  Then I add metadata "login_duration_ms" with value "250"
```

**Usage in Steps**:
```python
# In your step definitions
context.report_manager.add_metadata("key", "value")
```

**Benefits**:
- Add environment details (browser version, OS, deployment environment)
- Track test data identifiers (user IDs, order numbers, etc.)
- Record performance metrics (response times, resource usage)
- Provide contextual information for better traceability

#### Explicit Logging
```gherkin
# features/advanced_examples/explicit_logging.feature
Scenario: Checkout with step-by-step logging
  When I log message "Step 1: User logged in" at level "INFO"
  And I log message "Step 2: Product added to cart" at level "INFO"
  And I log message "Cart state updated" at level "DEBUG"
  Then I log message "Checkout completed successfully" at level "INFO"
```

**Log Levels Supported**:
- `INFO`: General informational messages
- `DEBUG`: Detailed debugging information
- `WARN`: Warning messages for unexpected behavior
- `ERROR`: Error conditions
- `TRACE`: Very detailed tracing information

**Usage in Steps**:
```python
context.report_manager.log_message("Your message", level="INFO")
```

#### Data-Driven Testing
```gherkin
# features/advanced_examples/data_driven.feature
Scenario Outline: Login with multiple valid users
  When I login with username "<username>" and password "<password>"
  Then I should see the products page

  Examples: Valid Users
    | username                | password     |
    | standard_user           | secret_sauce |
    | problem_user            | secret_sauce |
    | performance_glitch_user | secret_sauce |
```

**Benefits**:
- Each example creates a separate test in ReportPortal
- Parameters visible in test names
- Better test coverage with minimal code

### 3. Advanced Tag Support

#### @attribute Tags
```gherkin
@attribute(priority:high) @attribute(component:authentication)
Feature: User Authentication
```

**Effect**: Tags appear as attributes in ReportPortal for filtering and analytics

#### @test_case_id Tags
```gherkin
@test_case_id(TC-LOGIN-001)
Scenario: Successful login
```

**Effect**: Links test to test case management system

#### @fixture Tags
```gherkin
@fixture.database @fixture.cache
Scenario: Test with fixtures
```

**Effect**: Marks tests that use specific fixtures

### 4. Configuration Options

#### Step Log Layout
```yaml
# config/reporting.yaml
reportportal:
  step_log_layout: NESTED  # Options: SCENARIO, STEP, NESTED
```

- **SCENARIO**: Steps logged as messages only (compact view)
- **STEP**: Steps as flat test items under scenario
- **NESTED**: Steps as nested test items (hierarchical, most detailed)

#### Skip Handling
```yaml
reportportal:
  is_skipped_an_issue: false  # Don't mark skipped tests as issues
```

- `false`: Skipped tests are NOT marked as issues
- `true`: Skipped tests ARE marked as issues

#### Debug Mode
```yaml
reportportal:
  debug_mode: false  # Create DEBUG launches for testing
```

- `false`: Creates DEFAULT launches (production)
- `true`: Creates DEBUG launches (development/testing)

### 5. Running Examples

#### Run Metadata Demo
```bash
nemesis run --feature advanced_examples/metadata_demo.feature
```

#### Run Logging Demo
```bash
nemesis run --feature advanced_examples/explicit_logging.feature
```

#### Run Data-Driven Tests
```bash
nemesis run --feature advanced_examples/data_driven.feature
```

#### Run All Advanced Examples
```bash
nemesis run --tags @advanced
```

### 6. ReportPortal Dashboard

After running tests, view results in ReportPortal:

1. **Launches**: View all test executions
2. **Filters**: Filter by tags, attributes, status
3. **Trends**: Analyze test stability over time
4. **Widgets**: Create custom dashboards
5. **Defects**: Track known issues and their status

## ⚙️ Configuration

### Environment Variables
```bash
# Basic Settings
TEST_ENV=dev
BROWSER_TYPE=chromium
HEADLESS=false

# ReportPortal (Optional)
RP_ENABLED=false
RP_ENDPOINT=https://your-reportportal.com
RP_PROJECT=your-project-name
RP_API_KEY=your-api-key-here

# Reporting
REPORT_MODE=all
LOG_LEVEL=INFO
DEBUG=false
```

### Environment-Specific Settings

#### Development (`config/environments/dev.yaml`)
- Headless: `false`
- Slow motion: `1000ms`
- Debug: `enabled`
- Console capture: `true`

#### Staging (`config/environments/staging.yaml`)
- Headless: `true`
- Timeouts: `45s`
- Debug: `disabled`
- Network capture: `false`

#### Production (`config/environments/prod.yaml`)
- Headless: `true`
- Timeouts: `60s`
- Debug: `disabled`
- Minimal logging: `WARNING`

## 🔧 Troubleshooting

### Common Issues

#### 1. Module Not Found
```bash
# Solution: Install nemesis framework
cd ../nemesis
pip install -e .
```

#### 2. Browser Not Found
```bash
# Solution: Install Playwright browsers
playwright install chromium
```

#### 3. Config File Not Found
```bash
# Solution: Ensure you're in project directory
cd saucedemo-automation
ls -la config/
```

#### 4. Permission Denied
```bash
# Solution: Fix permissions
chmod -R 755 reports/
chmod -R 755 logs/
```

## 📈 Best Practices

### 1. Test Organization
- Use descriptive scenario names
- Group related scenarios with tags
- Keep steps reusable and maintainable

### 2. Page Objects
- Follow single responsibility principle
- Use meaningful selectors
- Implement proper waits and assertions

### 3. Configuration
- Use environment-specific configs
- Use environment variables for sensitive data
- Version control configuration templates

### 4. Reporting
- Enable appropriate artifacts for your needs
- Clean up old reports regularly
- Use ReportPortal for team collaboration

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
name: SauceDemo Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd nemesis && pip install -e .
          playwright install chromium
      - name: Run tests
        run: |
          cd saucedemo-automation
          nemesis run --headless -r all
```

## 📚 Documentation

- **Nemesis Framework**: [Framework Documentation](../nemesis/README.md)
- **Behave**: https://behave.readthedocs.io/
- **Playwright**: https://playwright.dev/python/
- **ReportPortal**: https://reportportal.io/docs/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**Happy Testing! 🎉**

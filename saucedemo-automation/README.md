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

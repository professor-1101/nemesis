# Nemesis Test Automation Framework

A powerful BDD test automation framework built with Behave and Playwright, featuring comprehensive reporting and artifact collection.

## Features

- 🎭 **Playwright Integration**: Modern browser automation
- 🥒 **BDD with Behave**: Gherkin-based test scenarios
- 📊 **Multi-Reporter Support**: Local HTML, ReportPortal
- 📈 **Performance Metrics**: Navigation timing, resource timing
- 🌐 **Network Monitoring**: HAR files, request/response tracking
- 🖥️ **Console Logging**: Browser console error tracking
- 🎥 **Video Recording**: Test execution videos with mouse tracking
- 📸 **Screenshots**: Automatic screenshot capture on failure
- 🔍 **Trace Files**: Playwright trace viewer support
- 🚀 **Beautiful CLI**: Rich console output with progress tracking

## Installation

### Framework Installation

```bash
pip install nemesis-automation
```

**Important:** Environment variables (like `JAVA_HOME`) are inherited by Python processes, but you may need to:

1. **Restart your terminal/PowerShell** after setting environment variables in System Properties
2. **Or set them in the current session** before running tests:

```bash
# Windows PowerShell (current session only)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Linux/macOS (current session only)
export JAVA_HOME=/path/to/jdk-17
export PATH=$JAVA_HOME/bin:$PATH
```

3. **For permanent setup**, add to System Environment Variables (Windows) or `~/.bashrc`/`~/.zshrc` (Linux/macOS)

### Allure CLI Installation (Optional)

For full-featured Allure HTML reports with Dashboard, Charts, and Timeline, you need to install Java and Allure CLI separately:

**Prerequisites:**
- Java JDK 17 LTS (required for Allure CLI)
- Set `JAVA_HOME` environment variable

**Install Java 17 LTS:**
- **Recommended:** Download from [Eclipse Temurin JDK 17 LTS](https://adoptium.net/temurin/releases/)
- Windows: Download `.msi` installer from Adoptium
- macOS: `brew install --cask temurin17` or download from Adoptium
- Linux: Download from Adoptium or use package manager

**Install Allure CLI:**

**Windows:**
```bash
# Using Chocolatey
choco install allure

# Using Scoop
scoop install allure

# Using npm
npm install -g allure-commandline
```

**macOS:**
```bash
brew install allure
```

**Linux:**
```bash
npm install -g allure-commandline
```

**Manual Installation:**
Download from [Allure Releases](https://github.com/allure-framework/allure2/releases) and add to PATH.

After installation, verify:
```bash
java -version
allure --version
```

**Note:** If you see "JAVA_HOME is not set" error, you need to:
1. Install Java JDK 17 LTS from [Eclipse Temurin](https://adoptium.net/temurin/releases/)
2. Set `JAVA_HOME` environment variable to your Java installation path (e.g., `C:\Program Files\Eclipse Adoptium\jdk-17.x.x-hotspot`)
3. Add `%JAVA_HOME%\bin` (Windows) or `$JAVA_HOME/bin` (Linux/macOS) to PATH

The framework will generate Allure results (JSON files) automatically. If Allure CLI is installed and Java is available, full HTML reports will be generated. Otherwise, a simple fallback HTML report will be created with instructions.

**Viewing Allure Reports:**

Due to CORS restrictions, you cannot open Allure reports directly with `file://` protocol. Use one of these methods:

**Method 1: Using Allure CLI (Recommended)**
```bash
cd reports/YYYY-MM-DD_HH-MM-SS_<execution-id>
allure open allure-report
```
This starts a local HTTP server and opens the report in your browser.

**Method 2: Using Python HTTP Server**
```bash
# Python 3
cd reports/YYYY-MM-DD_HH-MM-SS_<execution-id>
python -m http.server 8000
# Then open http://localhost:8000/report.html in your browser
```

**Method 3: Using Node.js http-server**
```bash
npm install -g http-server
cd reports/YYYY-MM-DD_HH-MM-SS_<execution-id>
http-server -p 8000
# Then open http://localhost:8000/report.html in your browser
```

## Quick Start

```bash
# Install Playwright browsers
playwright install chromium

# Run tests
nemesis run

# Run with specific tags
nemesis run --tags @smoke

# Run with specific environment
nemesis run --env staging

# View recent executions
nemesis list

# Clean old reports
nemesis clean --older-than 7d
```

## Configuration

Framework uses YAML configuration files:

- `playwright.yaml`: Browser settings
- `reporting.yaml`: Report configuration
- `reportportal.yaml`: ReportPortal settings
- `environments/*.yaml`: Environment-specific configs

## Report Modes

- `local`: HTML reports with artifacts
- `reportportal`: Real-time reporting to ReportPortal
- `all`: All reporters enabled (default)

## CLI Options

```bash
nemesis run [OPTIONS]

Options:
  -t, --tags TEXT         Run scenarios with specific tags
  -f, --feature TEXT      Run specific feature file
  -e, --env TEXT         Environment (dev/staging/prod)
  -r, --report TEXT      Report mode (local/reportportal/all)
  -p, --parallel INT     Number of parallel workers
  --headless/--no-headless  Run in headless mode
  --dry-run              Validate without execution
  --debug                Enable debug logging
```

## License

MIT License
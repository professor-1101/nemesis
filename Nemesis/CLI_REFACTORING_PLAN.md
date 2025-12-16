# Nemesis CLI Refactoring Plan
## Cypress-like Experience with Clean Architecture

### 🎯 Goals

1. **Cypress-like UX**: Beautiful, intuitive, real-time feedback
2. **Clean Architecture**: Decouple CLI from framework internals
3. **Observability**: Distributed tracing, structured logging
4. **Full Documentation**: Complete user and developer docs

---

## 📐 Architecture Design (Clean Architecture)

### Current Issues ❌
- `run` command directly uses `TestExecutor` (old architecture)
- Tightly coupled to Behave internals
- No separation of concerns
- Hard to test and maintain

### New Architecture ✅

```
┌─────────────────────────────────────────────────────┐
│               CLI Layer (Presentation)               │
│  - Click commands (run, init, list, open, etc.)    │
│  - Rich UI (progress bars, tables, colors)         │
│  - User input validation                            │
└──────────────────┬──────────────────────────────────┘
                   │ Uses
                   ▼
┌─────────────────────────────────────────────────────┐
│           Application Layer (Use Cases)              │
│  - RunTestsUseCase                                  │
│  - GenerateReportUseCase                            │
│  - InitializeProjectUseCase                         │
│  - Coordinators (ExecutionCoordinator, etc.)        │
└──────────────────┬──────────────────────────────────┘
                   │ Uses
                   ▼
┌─────────────────────────────────────────────────────┐
│              Domain Layer (Entities)                 │
│  - Execution, Scenario, Step                        │
│  - Value Objects (ExecutionId, Duration, etc.)      │
│  - Ports (IBrowserDriver, IReporter, ICollector)    │
└──────────────────┬──────────────────────────────────┘
                   │ Implemented by
                   ▼
┌─────────────────────────────────────────────────────┐
│         Infrastructure Layer (Adapters)              │
│  - PlaywrightBrowserDriver                          │
│  - JSONReporter, ConsoleReporter                    │
│  - SigNozShipper, LocalFileShipper                  │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Cypress-like Features

### 1. Real-Time Execution Feedback
```bash
$ nemesis run

  ┌────────────────────────────────────────┐
  │   Running: Login Feature (1 of 3)      │
  └────────────────────────────────────────┘

    ✓ User can login with valid credentials   2.3s
      ✓ Given I am on login page              0.5s
      ✓ When I enter valid credentials        0.8s
      ✓ Then I should see dashboard           1.0s

    ✗ User cannot login with invalid password 1.5s
      ✓ Given I am on login page              0.5s
      ✗ When I enter invalid password         0.5s
        AssertionError: Expected error message not displayed

  ┌────────────────────────────────────────┐
  │   Test Results                          │
  ├────────────────────────────────────────┤
  │   Passing:     15    │   Duration: 23s │
  │   Failing:      2    │   Browser: chromium
  │   Skipped:      1    │                  │
  └────────────────────────────────────────┘

  📹  Video:  reports/exec_20251216_120000/videos/login.mp4
  📊  Report: reports/exec_20251216_120000/index.html
```

### 2. Interactive Mode
```bash
$ nemesis run --interactive
# Watch mode: re-run on file changes
# Keyboard shortcuts: r (re-run), s (stop), o (open report)
```

### 3. Smart Defaults (like Cypress)
- Auto-detect browser from config
- Auto-open report on completion
- Auto-retry flaky tests
- Smart parallelization

### 4. Beautiful Error Messages
```bash
✗ Login test failed

  Error: Element not found: #login-button

  Selector: #login-button
  Expected: Element to be visible
  Actual:   Element not found in DOM

  Screenshot: reports/screenshots/login-error-001.png
  Video:      reports/videos/login-001.mp4
  Trace:      reports/traces/login-001.zip

  Stack:
    at Page.click (login_steps.py:45)
    at step_impl (login_steps.py:42)
```

---

## 🔧 Implementation Steps

### Phase 1: Refactor `run` Command ✅
**Files to modify:**
- `src/nemesis/cli/commands/run.py` - Use RunTestsUseCase instead of TestExecutor
- Create `src/nemesis/application/use_cases/run_tests.py` - New use case
- Update `src/nemesis/cli/ui/` - Enhanced progress bars, live updates

**Changes:**
```python
# OLD (Direct coupling)
executor = TestExecutor(config)
exit_code = executor.execute()

# NEW (Clean Architecture)
use_case = RunTestsUseCase(
    browser_driver=PlaywrightBrowserDriver(),
    reporters=[ConsoleReporter(), JSONReporter(output_dir)],
    collectors=[],
    config=config
)
execution = use_case.execute(
    tags=tags,
    feature=feature,
    env=env
)
```

### Phase 2: Add Real-Time Progress ✅
**Features:**
- Live scenario/step progress bars
- Real-time pass/fail counters
- Elapsed time tracking
- Browser activity indicator

**Implementation:**
- Use Rich library's `Live` display
- Update progress in reporter callbacks
- Show screenshots/videos as they're captured

### Phase 3: Observability & Tracing ✅
**Add distributed tracing:**
- OpenTelemetry integration
- Span creation for execution/scenario/step
- Export to SigNoz/Jaeger
- Correlation IDs across logs

**Files to create:**
- `src/nemesis/infrastructure/observability/tracer.py`
- `src/nemesis/infrastructure/observability/metrics.py`

### Phase 4: Documentation ✅
**Create comprehensive docs:**
- `docs/cli/README.md` - CLI overview
- `docs/cli/commands.md` - All commands reference
- `docs/cli/configuration.md` - Config options
- `docs/architecture/cli.md` - Architecture diagram

---

## 📝 Cypress-like Commands

### Comparison Table

| Cypress | Nemesis | Description |
|---------|---------|-------------|
| `cypress open` | `nemesis open` | Open interactive UI |
| `cypress run` | `nemesis run` | Run all tests |
| `cypress run --spec` | `nemesis run --feature` | Run specific test |
| `cypress run --headed` | `nemesis run --headed` | Run in headed mode |
| `cypress run --browser` | `nemesis run --browser` | Select browser |
| N/A | `nemesis run --tags` | Run by tags (BDD feature) |

---

## 🎯 Success Criteria

✅ Run command uses Clean Architecture (Application layer)
✅ Real-time progress with Rich UI
✅ Beautiful error messages with context
✅ Auto-open reports after execution
✅ Distributed tracing integration
✅ Comprehensive documentation
✅ 100% test coverage for CLI layer

---

## 🚀 Quick Start After Refactoring

```bash
# Initialize new project
nemesis init

# Run all tests (Cypress-like experience)
nemesis run

# Run with specific tags
nemesis run --tags @smoke

# Watch mode (re-run on changes)
nemesis run --watch

# Interactive mode
nemesis open

# Generate report
nemesis report --open
```

---

## 📊 Metrics & Observability

### Metrics to Track
- Test execution duration
- Scenario pass/fail rate
- Step execution time
- Browser launch time
- Network requests count
- Screenshots/videos captured

### Distributed Tracing
- Execution span (root)
  - Scenario spans (children)
    - Step spans (grandchildren)

### Structured Logging
```json
{
  "timestamp": "2025-12-16T12:00:00Z",
  "level": "INFO",
  "execution_id": "exec_20251216_120000",
  "scenario_id": "scenario_abc123",
  "step_id": "step_xyz789",
  "event": "step_completed",
  "duration_ms": 1500,
  "status": "passed"
}
```

---

## 🎨 UI/UX Principles (Cypress-inspired)

1. **Visual Clarity**: Use colors, icons, emojis
2. **Real-Time Feedback**: Show progress as it happens
3. **Helpful Errors**: Context, screenshots, suggestions
4. **Smart Defaults**: Minimize required flags
5. **Keyboard Shortcuts**: Power user features
6. **Documentation**: Built-in help text


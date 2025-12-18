# Changelog

All notable changes to the Nemesis Test Automation Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Exception handling decorators (`@handle_exceptions` and `@handle_exceptions_with_fallback`) for DRY exception management
- Four new helper methods in `ReporterCoordinator` with exception decorators for cleaner initialization
- Comprehensive dead code analysis using Vulture

### Changed
- **Breaking**: Removed unused `reason` parameter from `Scenario.fail()` method
  - Migration: Update all calls from `scenario.fail("reason")` to `scenario.fail()`
  - Rationale: Parameter was never used in implementation (identified by Vulture analysis)

- Applied exception handling decorators to 16 files across codebase:
  - **Infrastructure** (4 files):
    - `config/loader.py`: 5 config loading methods
    - `browser/collector_coordinator.py`: 3 coordinator methods
    - `collectors/console.py`: 2 collector methods
    - `collectors/network.py`: dispose method

  - **Reporting & Hooks** (7 files):
    - `reporting/management/feature_handler.py`: Extracted helper methods
    - `reporting/management/scenario_handler.py`: Extracted helper methods
    - `reporting/management/step_handler.py`: Extracted helper methods
    - `infrastructure/environment/feature_hooks.py`: Hook functions
    - `infrastructure/environment/scenario_hooks.py`: after_scenario hook
    - `infrastructure/environment/hooks.py`: after_all hook
    - `infrastructure/environment/step_hooks.py`: Hook functions

  - **CLI & Attachments** (2 files):
    - `reporting/management/attachments/metrics_handler.py`: Extracted helper methods
    - `cli/commands/run.py`: _show_report_path function

  - **Browser Operations** (2 files):
    - `browser/browser_operations.py`: get_video_path method
    - `browser/video_processing_service.py`: Video conversion methods

  - **Reporter Coordination** (1 file):
    - `reporting/management/reporter_coordinator.py`: Extracted 4 helper methods

### Removed
- Unused imports identified by Vulture analysis:
  - `Tree` from `cli/ui/live_reporter.py`
  - `StepHandler` from `reporting/coordinator.py`
  - `traceback` from 3 refactored files (decorators now handle exception logging):
    - `browser/browser_operations.py`
    - `browser/video_processing_service.py`
    - `reporting/management/reporter_coordinator.py`
- Unused parameter `error_context` from `feature_handler._call_rp_client()`
- Unused parameter `reason` from `Scenario.fail()` method

### Fixed
- Circular import issue in `timeout_decorators.py`:
  - Changed import from `nemesis.shared.exceptions` to `nemesis.shared.exceptions.network_exceptions`
  - Removed `DirectoryService` from `shared/__init__.py` to break dependency cycle
- Updated 6 test files to match new `Scenario.fail()` signature (removed unused reason parameter)

### Performance
- Reduced code duplication by ~180 lines through exception decorator application
- Eliminated 7 instances of dead code improving maintainability
- Cleaner exception handling with consistent logging patterns

### Developer Experience
- More maintainable exception handling with centralized decorator logic
- Reduced boilerplate in exception handling by 30-50% in refactored files
- Improved code readability through method extraction pattern
- Zero regression - all 210 tests passing after refactoring

## Technical Details

### Exception Decorator Infrastructure

Two decorators were systematically applied across the codebase:

1. **`@handle_exceptions`**: For methods that should log exceptions and continue
   ```python
   @handle_exceptions(
       log_level="error",
       catch_exceptions=(OSError, IOError)
   )
   def some_method(self):
       # Method body without try-except
   ```

2. **`@handle_exceptions_with_fallback`**: For methods that return default values on error
   ```python
   @handle_exceptions_with_fallback(
       log_level="warning",
       specific_exceptions=(AttributeError, RuntimeError),
       specific_message="Operation failed: {error}",
       return_on_error=None
   )
   def get_optional_value(self):
       # Method body without try-except
   ```

### Refactoring Impact Summary

| Phase | Files | Lines Saved | Focus Area |
|-------|-------|-------------|------------|
| Phase 1 | 4 | -85 | Infrastructure (Config, Collectors) |
| Phase 2 | 7 | -54 | Reporting & Hooks |
| Phase 3 | 2 | -16 | CLI & Attachments |
| Phase 4 | 2 | -25 | Browser Operations |
| Phase 5 | 1 | +9* | Reporter Coordination (quality improvement) |
| **Total** | **16** | **~180** | **Across all layers** |

*Note: Phase 5 improved code organization through method extraction, which slightly increased total lines while significantly improving maintainability.

### Dead Code Removal

Vulture analysis identified and removed:
- 4 unused imports
- 2 unused method parameters
- 1 unused class parameter
- All findings verified and removed with zero test failures

### Testing

- All 210 existing tests continue to pass
- No new test failures introduced
- No behavioral changes - only refactoring
- Exception handling behavior preserved through decorators

### Migration Notes

#### For Scenario.fail() Usage

**Before:**
```python
scenario.fail("Test failed due to assertion error")
```

**After:**
```python
scenario.fail()  # Reason parameter removed (was never used)
```

**Impact**: Low - parameter was never actually used in implementation, only accepted and ignored.

---

## [Previous Versions]

This is the first CHANGELOG entry. Previous changes were not documented in a structured format.

For historical changes, see:
- Git commit history: `git log`
- Architecture documentation: `/docs/architecture/`
- DoD compliance summary: `/docs/architecture/dod-compliance-summary.md`

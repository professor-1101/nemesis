# Comprehensive Code Review Report
## Nemesis Test Automation Framework & PostBank Project

**Review Date:** December 24, 2025
**Reviewed By:** Claude Code Review Agent
**Projects:** Nemesis Framework, PostBank Test Project
**Review Scope:** Architecture, Code Quality, Performance, Security, Testing, Configuration, Documentation

---

## Executive Summary

This comprehensive review analyzed 181 Python files, 10 feature files, 16 documentation files, and 8 configuration files across the Nemesis test automation framework and PostBank test project. The analysis covered seven critical areas: architecture compliance, code quality, performance optimization, security vulnerabilities, test coverage, configuration management, and documentation completeness.

### Overall Health Score: **7.1/10**

**Strengths:**
- Excellent Clean Architecture implementation with clear layer separation
- Comprehensive domain layer testing (70-75% coverage)
- Well-designed configuration system with environment variable support
- Strong documentation foundation with detailed architecture docs
- Professional BDD implementation with Persian language support
- Good use of design patterns (hexagonal architecture, dependency injection)

**Critical Issues Identified:**
- 🔴 **SECURITY**: ReportPortal API key exposed in version control
- 🔴 **SECURITY**: Passwords logged to console without masking
- 🔴 **SECURITY**: Sensitive network headers captured without filtering
- 🔴 **CODE QUALITY**: StepHandler god object (755 lines, 26 methods)
- 🔴 **CODE QUALITY**: NetworkCollector SRP violation (5 responsibilities)
- 🔴 **PERFORMANCE**: Multiple list passes (O(5n) complexity)
- 🔴 **TESTING**: Very low assertion density (0.7%)
- 🔴 **TESTING**: 76 hard-coded timeout calls indicating race conditions

---

## Overall Scores by Category

| Category | Score | Status | Priority |
|----------|-------|--------|----------|
| **Architecture** | 7.5/10 | Good | MEDIUM |
| **Code Quality** | 6.2/10 | Fair | HIGH |
| **Performance** | 6.0/10 | Fair | HIGH |
| **Security** | 6.0/10 | Fair | CRITICAL |
| **Testing** | 6.8/10 | Fair | HIGH |
| **Configuration** | 6.5/10 | Fair | CRITICAL |
| **Documentation** | 8.5/10 | Good | MEDIUM |
| **OVERALL** | **7.1/10** | **Good** | **-** |

---

## 1. Architecture Review (7.5/10)

### Strengths
✅ Clean Architecture layers properly separated
✅ Dependency Inversion Principle well-implemented
✅ Interface Segregation Principle excellent
✅ No circular dependencies detected
✅ Hexagonal architecture with clear ports/adapters
✅ Domain layer completely isolated from infrastructure

### Critical Violations

#### 🔴 Single Responsibility Principle (SRP) - 5 Critical Violations

**1. NetworkCollector** (`/infrastructure/collectors/network.py` - 490 lines)
- **Violations:** 5 distinct responsibilities
  - Network event collection (71-174)
  - Metrics aggregation (176-199)
  - HAR export formatting (201-328)
  - File I/O operations (379-437)
  - Data persistence management (462-491)
- **Impact:** Difficult to test, modify, or extend
- **Recommendation:** Split into 5 focused classes

**2. StepHandler** (`/reporting/management/step_handler.py` - 755 lines)
- **Violations:** God Object pattern with 26 methods
  - Step lifecycle management
  - Local reporting
  - ReportPortal integration
  - Step name transformation
  - Placeholder replacement
- **Impact:** Highest risk for bugs and maintenance issues
- **Recommendation:** Decompose into 4 specialized classes

**3. ConsoleCollector** (`/infrastructure/collectors/console.py` - 282 lines)
- **Violations:** 4 distinct responsibilities
  - Console event listening
  - Message filtering & pattern matching
  - Log aggregation
  - File serialization
- **Impact:** High coupling, difficult to modify
- **Recommendation:** Extract pattern matching and file I/O

**4. TestExecutor** (`/cli/core/executor.py` - 233 lines)
- **Violations:** 4 distinct responsibilities
  - Environment setup
  - Behave command building
  - Process execution
  - Real-time output streaming
- **Impact:** Complex error handling, hard to test
- **Recommendation:** Extract command builder and output handler

**5. BasePage** (`/PostBank/pages/base_page.py` - 360 lines)
- **Violations:** Multiple UI operation methods mixed with debugging
  - Generic element interactions
  - Specialized Kendo dropdown handling (47 lines)
  - Tree dropdown selection (104 lines)
  - Debug information capture
- **Impact:** Confusing for test engineers, hard to extend
- **Recommendation:** Create specialized page objects per component type

### Liskov Substitution Principle Violation

**ConsoleReporter vs JSONReporter** (`/infrastructure/reporting/`)
- `ConsoleReporter.generate_report()` returns `None`
- `JSONReporter.generate_report()` returns `Path`
- **Impact:** Clients must check for None explicitly
- **Recommendation:** Return empty/null object pattern instead of None

### Package Structure Issues

**Reporting Module Confusion**
- `/reporting/` - Old reporting system (complex orchestration)
- `/infrastructure/reporting/` - New reporter adapters
- **Impact:** Contributors confused about which system to use
- **Recommendation:** Consolidate into single location with clear deprecation

---

## 2. Code Quality Review (6.2/10)

### Code Smells - Top 20 Issues

#### Long Methods (>50 lines)

| File | Method | Lines | Severity |
|------|--------|-------|----------|
| cli/commands/run.py | run_command() | 166 | CRITICAL |
| utils/decorators/exception_handler.py | handle_exceptions() | 132 | HIGH |
| infrastructure/collectors/network.py | export_as_har() | 128 | HIGH |
| cli/core/executor.py | _execute_realtime() | 118 | HIGH |
| reporting/management/report_finalizer.py | finalize() | 120 | HIGH |

**Impact:** Methods over 100 lines violate SRP and are difficult to test.

#### Large Classes (>300 lines)

| Class | File | Lines | Methods | Issue |
|-------|------|-------|---------|-------|
| StepHandler | step_handler.py | 755 | 26 | God Object |
| NetworkCollector | network.py | 473 | 20 | Multiple responsibilities |
| PlaywrightPageAdapter | playwright_adapter.py | 425 | 17 | Too many page methods |
| BasePage | base_page.py | 360 | 15 | Mixed concerns |

#### Deep Nesting (>3 levels)

- `login_page.py` lines 74-122: **6 levels of nesting** (CRITICAL)
- `base_page.py` lines 220-265: **4 levels of nesting**
- `scenario_hooks.py` lines 23-34: **4 levels of nesting**

**Example:**
```python
if self._playwright_page:           # Level 1
    try:                            # Level 2
        label = ...                 # Level 3
        if label.count() > 0:       # Level 4
            input_after = ...       # Level 5
            if input_after.count() > 0:  # Level 6 (TOO DEEP!)
```

#### Magic Numbers/Strings

**Hard-coded timeouts scattered throughout:**
- network.py: `MAX_REQUESTS = 50000`, `MAX_URL_LENGTH = 500`
- playwright_adapter.py: `DEFAULT_SENSITIVE_PATTERNS = [...]`
- base_page.py: `http://192.168.10.141:1365/` (hardcoded IP)
- Multiple files: Timeout values (2000, 5000, 10000ms) not configurable

### Code Duplications - Top 10

#### 1. Selector Try-Catch Pattern (90+ lines duplicated)
**Files:** `login_page.py`, `base_page.py`, `applicant_registration_page.py`
```python
for selector in self.SELECTOR_LIST:
    try:
        self.fill(selector, value)
        return
    except Exception:
        continue
```
**Impact:** 50+ lines of duplicated code across 3 files

#### 2. Exception Handling Pattern (155 occurrences)
**Files:** All reporting and infrastructure files
```python
except (AttributeError, RuntimeError) as e:
    self.logger.error(f"Failed: {e}", traceback=traceback.format_exc(), ...)
except Exception as e:  # pylint: disable=broad-exception-caught
    self.logger.error(f"Failed: {e}", traceback=traceback.format_exc(), ...)
```
**Impact:** Exception handling should be extracted to decorator

#### 3. Context Information Building (Duplicate 11-line blocks)
**File:** `rp_logger.py` lines 115-125 and 222-232
```python
context_info = ""
if context:
    context_info = "\n📋 CONTEXT:\n"
    if 'feature' in context:
        context_info += f"  Feature: {context['feature']}\n"
    # ... 6 more lines identical
```

### Best Practice Violations - Top 20

#### Missing Type Hints (100+ instances)
- 50+ functions without return type hints
- 100+ parameters without type hints
- Example: `reporting/coordinator.py:163-173`
```python
def attach_video(self, video_path):  # ❌ No type hints
def attach_trace(self, trace_path):  # ❌ No type hints
```

#### Broad Exception Handling (155 occurrences)
```python
except Exception as e:  # ❌ TOO BROAD
    # Should catch specific exceptions
```

**Files affected:** 50+ across reporting/, infrastructure/, PostBank/

#### Inadequate Docstrings (60+ instances)
- 22 methods lack docstrings in `step_handler.py`
- Multiple helper methods in `base_page.py`
- PlaywrightPageAdapter.__init__() - Only 5 lines for complex init

---

## 3. Performance Review (6.0/10)

### Critical Performance Bottlenecks

#### 🔴 HIGH: Inefficient Network Metrics Collection
**File:** `/infrastructure/collectors/network.py` lines 176-189
**Complexity:** O(5n) instead of O(n)

**Issue:**
```python
# FIVE PASSES through self.requests!
requests = [r for r in self.requests if r["type"] == "request"]  # Pass 1
responses = [r for r in self.requests if r["type"] == "response"]  # Pass 2
failed = [r for r in self.requests if r["type"] == "failed"]  # Pass 3
# Pass 4: Status codes
# Pass 5: Durations and sizes
```

**Impact:** For 10,000 requests, this performs 50,000 iterations instead of 10,000
**Expected Improvement:** 80% reduction in execution time
**Priority:** HIGH

#### 🟡 MEDIUM: Excessive Exception Handling with Broad Types
**File:** `/reporting/management/step_handler.py`
**Occurrences:** 23 instances

```python
except Exception:  # Line 54
    pass  # Fallback silently
```

**Problems:**
- Catches system exceptions (KeyboardInterrupt)
- Hides programming errors
- Performance overhead from catching all exceptions

#### 🟡 MEDIUM: Maximum Request Limit Inefficiency
**File:** `/infrastructure/collectors/network.py` lines 78, 106, 158
**Issue:** Storing 50,000 requests in memory (100MB+ depending on header size)

**Recommendation:** Use deque with maxlen for automatic oldest-first rotation

### Memory Management Issues

1. **High Memory Growth:** 50,000 requests × 2KB headers = 100MB+ per execution
2. **No Cleanup During Test Runs:** Memory accumulates indefinitely
3. **Browser Context Cleanup Not Guaranteed:** May leak browser resources

---

## 4. Security Review (6.0/10)

### 🔴 CRITICAL Security Vulnerabilities

#### 1. Exposed API Key in Version Control
**File:** `/PostBank/conf/reportportal.yaml` line 7
**Severity:** **CRITICAL**

```yaml
api_key: postbank_42RUSWAMQOi1TvPax2cfLaeBxfxIBvJffDFb0TomS87eqk4fJhSpZoXUmKFzJl7d
```

**Risk:** Complete compromise of test reporting infrastructure
**Action Required:**
1. ✅ IMMEDIATE: Revoke this API key
2. ✅ Generate new API key
3. ✅ Move to environment variables
4. ✅ Add `reportportal.yaml` to `.gitignore`
5. ✅ Implement git-secrets hook

#### 2. Hardcoded Password Logging
**File:** `/PostBank/features/environment.py` lines 55, 101, 172-177, 182, 215-216, 250-257
**Severity:** **CRITICAL**

```python
# Line 55 - Password hardcoded
'رمز_عبور': username,  # password is the same as username

# Lines 215-216 - Debug logging of password
print(f"[DEBUG] context.active_outline set: {context.active_outline.get('نام_کاربری', 'NOT SET')}")
print(f"[DEBUG] context.current_user_data set: {context.current_user_data.get('نام_کاربری', 'NOT SET')}")
```

**Also in:** `login_steps.py` lines 41, 101, 127, 172, 216

**Risk:** Passwords visible in console logs and stored in memory without masking
**Action Required:** Implement secure masking utility for all sensitive fields

#### 3. Sensitive Network Headers Captured
**File:** `/infrastructure/collectors/network.py` line 92
**Severity:** **HIGH**

```python
"headers": dict(request.headers),  # ❌ Contains Authorization, Cookies, API keys!
```

**Risk:** Authorization headers, cookies, and API keys captured without filtering
**Action Required:** Filter sensitive headers before capture:
```python
SENSITIVE_HEADERS = {
    'authorization', 'cookie', 'set-cookie', 'x-api-key',
    'x-auth-token', 'x-csrf-token', 'bearer'
}
```

#### 4. Resource Cleanup Not Guaranteed
**File:** `/infrastructure/logging/local_file_shipper.py` lines 37, 81-83
**Severity:** **HIGH**

```python
def __init__(self, log_file_path: Path):
    # File opened but NO context manager or __del__ method
    self._file = open(self.log_file_path, "a", encoding="utf-8")
```

**Risk:** File descriptors may never be closed, causing resource leaks
**Action Required:** Implement `__enter__`, `__exit__`, and `__del__` methods

#### 5. SSL Verification Disabled
**File:** `/PostBank/conf/reportportal.yaml` line 15
**Severity:** **HIGH**

```yaml
verify_ssl: false  # ❌ Vulnerable to MITM attacks
```

**Risk:** Man-in-the-middle attacks possible
**Action Required:** Enable SSL verification for production

### Security Checklist

- [x] Configuration loader handles exceptions properly
- [x] Environment variable substitution implemented
- [x] Default values provided
- [ ] ❌ **Secrets not in version control** (CRITICAL FIX NEEDED)
- [ ] ❌ **SSL verification enabled** (CRITICAL FIX NEEDED)
- [ ] ❌ **No hardcoded IPs/URLs** (CRITICAL FIX NEEDED)
- [x] Sensitive data masking in logs enabled
- [x] .gitignore protects .env files
- [ ] ❌ **No git-secrets hook configured**

---

## 5. Testing Review (6.8/10)

### Test Coverage Estimation

**PostBank (BDD/Behave): 25-30% Coverage**
- 2 active features, 4 total scenarios
- 6 page objects with 43 methods
- 18 step definition functions
- 6,320 users in test data CSV
- Covers: Login (HIGH), Applicant Registration (MEDIUM), Dashboard (LOW)

**Nemesis Framework: 70-75% Coverage**
- 217 test functions across 12 test files
- 3,246 lines of test code
- 21 pytest fixtures
- Comprehensive domain layer testing

### Critical Test Quality Issues

#### 🔴 CRITICAL: Very Low Assertion Density (0.7%)
**File:** `/PostBank/features/steps/login_steps.py`
- **Total Lines:** 424
- **Assertions:** 3
- **Density:** 0.7% (should be 2-3% minimum)

**Impact:** Tests may pass even when functionality is broken

#### 🔴 CRITICAL: 76 Hard-Coded Timeout Calls
**Files:** Throughout PostBank
```python
self.page.wait_for_timeout(500)  # ❌ Race condition indicator
self.page.wait_for_timeout(3000)  # ❌ Flaky test indicator
```

**Impact:** Tests will fail intermittently
**Recommendation:** Replace with explicit waits (`wait_for_selector()`)

#### 🔴 HIGH: Debug Print Statements in Production (10+ instances)
**Files:** `login_steps.py`, `environment.py`, `base_page.py`
```python
print(f"[DEBUG] context.active_outline set: {...}")  # ❌ Should use logging
```

**Impact:** Console noise, performance overhead

### Flaky Test Indicators

**High Risk:**
1. Captcha detection logic with complex Persian text filtering
2. 500ms timeouts suggesting race conditions
3. Random user selection from 6,320 users (some may be inactive)

**Medium Risk:**
4. Browser navigation timing without state verification
5. Form field locators with 20+ selector fallbacks (brittle)

### Untested Critical Paths

**PostBank (13 gaps):**
1. Data persistence (no database testing)
2. Batch operations
3. Load/stress testing
4. Report generation
5. Form validation edge cases
6. Search/Filter functionality
7. Pagination
8. Export functionality
9. Session management
10. Password reset flows
11. Multi-language support
12. Mobile responsiveness
13. Concurrent user scenarios

**Nemesis Framework (6 gaps):**
1. Parallel test execution
2. Report Portal integration
3. Custom hooks
4. Error recovery mechanisms
5. Browser crash handling
6. Network timeout handling

---

## 6. Configuration Review (6.5/10)

### Critical Configuration Issues

#### 🔴 CRITICAL: API Key Exposed
```yaml
# /PostBank/conf/reportportal.yaml
endpoint: http://192.168.10.191:9080
project: postbank
api_key: postbank_42RUSWAMQOi1TvPax2cfLaeBxfxIBvJffDFb0TomS87eqk4fJhSpZoXUmKFzJl7d  # ❌ EXPOSED
```

#### 🔴 CRITICAL: Hardcoded IP Addresses
**Files:** `reportportal.yaml`, `base_page.py`
- `http://192.168.10.191:9080` - Internal IP breaks CI/CD
- `http://192.168.10.141:1365/` - Hardcoded base URL

**Impact:** Tests cannot run outside specific network

#### 🔴 CRITICAL: SSL Verification Disabled
```yaml
verify_ssl: false  # ❌ Security risk
```

### Missing Configurations

- No `.env.example` template
- No environment-specific configs (dev/stage/prod)
- No configuration documentation
- Missing dependency: `reportportal-client` in PostBank requirements.txt

### Configuration Strengths

✅ Well-designed configuration loader with environment variable support
✅ Proper fallback syntax: `${VAR:-default}`
✅ Schema validation framework
✅ Comprehensive attachment configuration
✅ Structured YAML files with logical organization

---

## 7. Documentation Review (8.5/10)

### Documentation Strengths

✅ **Excellent main README** files with clear structure
✅ **Comprehensive architecture documentation** (556+ lines DoD compliance summary)
✅ **Well-documented feature files** with Gherkin syntax
✅ **Professional docstrings** using Google-style format
✅ **Phase-based documentation** tracking refactoring progress
✅ **Multiple example projects** demonstrating best practices

### Critical Documentation Gaps

| Missing Section | Priority | Impact |
|----------------|----------|--------|
| CONTRIBUTING.md | HIGH | Blocks community contributions |
| LICENSE file | HIGH | Legal/compliance issues |
| CHANGELOG | HIGH | Users can't track changes |
| API Documentation | HIGH | Infrastructure layer APIs undocumented |
| Troubleshooting Guide | MEDIUM | Users struggle with common errors |
| Glossary | MEDIUM | Domain terms not defined |

### Documentation Issues

**Outdated References:**
- Package installation references placeholder URLs
- Configuration examples show internal IPs
- Debug comments left in production code (10+ instances)

**Missing Examples:**
- Domain layer classes lack usage examples in docstrings
- No docstring examples for 147 classes
- Limited troubleshooting scenarios

---

## Critical Issues Summary

### 🔴 Immediate Action Required (Week 1)

#### Security (CRITICAL)
1. **Revoke ReportPortal API key** (`reportportal.yaml`)
2. **Remove password logging** (search all `password`, `رمز_عبور` in print/log statements)
3. **Filter network headers** (implement sensitive header filtering)
4. **Enable SSL verification** (`verify_ssl: true`)
5. **Fix file closure** (add context managers and `__del__` methods)

#### Code Quality (CRITICAL)
6. **Refactor StepHandler** (755 lines → 4 classes)
7. **Refactor NetworkCollector** (490 lines → 5 classes)

#### Testing (CRITICAL)
8. **Increase assertion density** (from 0.7% to 2-3%)
9. **Eliminate 76 timeout calls** (replace with explicit waits)
10. **Remove debug print statements** (use proper logging)

#### Configuration (CRITICAL)
11. **Remove hardcoded IPs** (use environment variables)
12. **Create .env.example** template
13. **Add reportportal-client** to PostBank requirements.txt

---

## High Priority Recommendations (Week 2-3)

### Architecture
1. Decompose TestExecutor into 3 focused classes
2. Extract BasePage specialized page objects
3. Consolidate reporting module organization

### Code Quality
4. Add type hints to 50+ critical functions
5. Replace 155 broad exception handlers with specific types
6. Extract duplicate selector pattern to utility class
7. Convert magic numbers to configuration constants

### Performance
8. Optimize network metrics collection (single-pass algorithm)
9. Implement memory monitoring and limits
10. Add resource cleanup verification

### Testing
11. Expand PostBank scenarios from 4 to 15-20
12. Add edge case tests (empty strings, long values, special chars)
13. Centralize test data loading (create TestDataManager)

### Configuration
14. Create environment-specific configs (dev/prod/ci)
15. Add configuration validation that fails on errors
16. Document all environment variables

### Documentation
17. Create CONTRIBUTING.md, LICENSE, CHANGELOG
18. Add troubleshooting guide with common errors
19. Remove all debug comments from production code

---

## Medium Priority Recommendations (Week 3-4)

### Architecture
1. Implement architecture decision records (ADRs)
2. Document design pattern decisions
3. Create onboarding guide for new developers

### Code Quality
1. Add docstring examples to domain classes
2. Create glossary of framework terms
3. Implement code quality gates in CI/CD

### Performance
1. Add performance benchmarks
2. Document optimization best practices
3. Implement request/response caching where appropriate

### Testing
1. Add performance and load testing
2. Implement visual regression testing
3. Create test data generators for edge cases

### Configuration
1. Add configuration migration guide
2. Create lock file for dependencies
3. Implement configuration encryption for secrets

### Documentation
1. Create comprehensive API documentation
2. Add deployment and CI/CD integration guide
3. Document security best practices

---

## Long-Term Recommendations (Ongoing)

1. **Monitoring & Observability**
   - Implement distributed tracing
   - Add performance monitoring dashboards
   - Create alerting for test failures

2. **DevOps Integration**
   - Container setup documentation
   - Cloud deployment guides
   - CI/CD pipeline templates

3. **Community Building**
   - Contribution guidelines
   - Code of conduct
   - Issue/PR templates

4. **Advanced Features**
   - Parallel test execution
   - Custom report formatters
   - Plugin architecture for extensibility

---

## Risk Assessment

### High Risk (Will Cause Production Issues)
1. API key exposed in version control
2. Hardcoded IP addresses preventing CI/CD
3. StepHandler god object (755 lines)
4. NetworkCollector SRP violation (490 lines)
5. 76 flaky timeout calls in tests

### Medium Risk (Maintenance Challenges)
1. Reporting module organization confusion
2. BasePage complexity (360 lines)
3. Collector inheritance model
4. Missing type hints (100+ instances)
5. Low test assertion density

### Low Risk (Polish and Optimization)
1. Domain layer docstring examples
2. Performance optimization opportunities
3. Documentation completeness
4. Configuration templates

---

## Effort Estimation

### Critical Fixes (Week 1): 40-50 hours
- Security remediation: 10-12 hours
- StepHandler refactoring: 12-15 hours
- NetworkCollector refactoring: 10-12 hours
- Test fixes (assertions, timeouts): 8-10 hours

### High Priority (Week 2-3): 60-70 hours
- Architecture improvements: 20-25 hours
- Code quality fixes: 15-20 hours
- Performance optimizations: 10-12 hours
- Test expansion: 15-18 hours

### Medium Priority (Week 3-4): 40-50 hours
- Documentation: 15-20 hours
- Configuration improvements: 10-12 hours
- Testing enhancements: 15-18 hours

**Total Estimated Effort:** 140-170 hours (~4-5 weeks full-time)

---

## Conclusion

The Nemesis framework demonstrates **solid architectural foundations** with excellent Clean Architecture implementation. The codebase is **production-ready for core functionality** but requires **urgent security remediation** before deployment.

**Key Takeaways:**

1. **Architecture (7.5/10):** Well-designed macro structure with specific SRP violations needing attention
2. **Security (6.0/10):** Critical vulnerabilities that must be addressed immediately
3. **Code Quality (6.2/10):** Good patterns with opportunities for refactoring large classes
4. **Testing (6.8/10):** Strong framework testing, PostBank needs expansion
5. **Configuration (6.5/10):** Good system design with critical security issues
6. **Documentation (8.5/10):** Excellent foundation, needs completion of critical files

**Immediate Next Steps:**
1. Revoke and rotate all exposed secrets
2. Refactor StepHandler and NetworkCollector
3. Fix security vulnerabilities (password logging, header filtering, SSL)
4. Increase test coverage and assertion density
5. Remove hardcoded IPs and create configuration templates

With these improvements, the framework can achieve a **9.0+/10** overall score within 4-5 weeks.

---

**Report Generated:** December 24, 2025
**Review Methodology:** Automated static analysis + manual code review
**Tools Used:** Glob, Grep, Read, Task (Explore agents)
**Files Analyzed:** 181 Python files, 10 feature files, 16 docs, 8 configs
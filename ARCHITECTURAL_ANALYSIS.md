# گزارش تحلیل معماری جامع - Nemesis Test Automation Framework
# Comprehensive Architectural Analysis - Nemesis Test Automation Framework

**تاریخ تحلیل**: 2025-12-16
**نسخه فریمورک**: 1.0.0
**تحلیلگر**: Software Architecture & Test Automation Lead
**هدف**: تحلیل انتقادی معماری بر اساس DDD، Clean Architecture، SOLID، و Clean Code

---

## 📊 خلاصه اجرایی | Executive Summary

### وضعیت کلی معماری: ⚠️ **نیازمند بازسازی اساسی**

فریمورک Nemesis از نظر عملکرد (functionality) کامل است اما از نظر معماری دارای **نقایص بنیادی** است که نگهداری، تست، و توسعه آن را بسیار دشوار می‌کند.

### مشکلات کلیدی:

| مشکل | شدت | تأثیر |
|------|-----|--------|
| عدم وجود Domain Model | 🔴 CRITICAL | Maintainability, Testability |
| وابستگی معکوس لایه‌ها | 🔴 CRITICAL | Framework Lock-in, Flexibility |
| God Classes | 🔴 CRITICAL | Complexity, SRP Violation |
| Primitive Obsession | 🟡 MAJOR | Type Safety, Business Rules |
| عدم Abstraction Boundaries | 🔴 CRITICAL | Extensibility, Testing |
| Circular Dependencies | 🟡 MAJOR | Maintainability |

---

## 1️⃣ DDD VIOLATIONS - نقض اصول Domain-Driven Design

### 1.1 ❌ CRITICAL: عدم وجود Domain Model

**مشکل**: هیچ مدل دامنه‌ای (Domain Model) مشخصی وجود ندارد. منطق کسب‌وکار (Business Logic) پخش شده در لایه Infrastructure است.

**شواهد**:

```python
# ❌ BAD: src/nemesis/reporting/local/data_model.py
@dataclass
class ScenarioData:
    """مدل بدون رفتار (Anemic Model)"""
    name: str
    start_time: datetime
    end_time: datetime | None = None
    status: str = "RUNNING"  # ⚠️ String primitive, not type-safe
    steps: list[StepData] = field(default_factory=list)

    # ⚠️ هیچ متد business logic ندارد!
```

**چرا اشتباه است**:
- `ScenarioData` یک data bag خالی است بدون هیچ رفتاری
- وضعیت (`status`) یک string primitive است نه یک Value Object
- قواعد کسب‌وکار (مثلاً "سناریو failed است اگر یک step fail شود") در این model نیست

**تأثیر**:
- **Maintainability**: منطق کسب‌وکار پراکنده در همه‌جا
- **Testability**: نمی‌توان منطق دامنه را به‌صورت مستقل تست کرد
- **Type Safety**: خطاهای runtime به دلیل عدم type-safety

---

### 1.2 ❌ CRITICAL: Anemic Domain Model

**مشکل**: تمام مدل‌های دامنه فقط data structure هستند بدون behavior.

```python
# ❌ BAD: ExecutionData هم فقط data holder است
@dataclass
class ExecutionData:
    execution_id: str  # ⚠️ Primitive, not ExecutionId value object
    start_time: datetime
    end_time: datetime | None = None
    scenarios: list[ScenarioData] = field(default_factory=list)

    @property
    def passed_scenarios(self) -> int:
        """شمردن سناریوهای موفق"""
        return sum(1 for s in self.scenarios if s.status == "PASSED")
        # ⚠️ منطق کسب‌وکار در property نه در method!
```

**چگونه باید باشد**:

```python
# ✅ GOOD: Rich Domain Model
class Scenario(Entity):
    """Scenario is a domain entity with behavior"""

    def __init__(self, scenario_id: ScenarioId, name: str):
        self._id = scenario_id
        self._name = name
        self._status = ScenarioStatus.PENDING
        self._steps: list[Step] = []
        self._domain_events: list[DomainEvent] = []

    def start(self) -> None:
        """شروع سناریو"""
        self._status = ScenarioStatus.RUNNING
        self._start_time = datetime.now(timezone.utc)
        self._domain_events.append(ScenarioStarted(self._id))

    def add_step(self, step: Step) -> None:
        """افزودن step"""
        self._steps.append(step)

    def fail(self, reason: str) -> None:
        """علامت‌گذاری به عنوان failed"""
        self._status = ScenarioStatus.FAILED
        self._end_time = datetime.now(timezone.utc)
        self._domain_events.append(ScenarioFailed(self._id, reason))

    def is_completed(self) -> bool:
        """آیا تمام steps اجرا شده‌اند؟"""
        return all(step.is_completed() for step in self._steps)

    @property
    def status(self) -> ScenarioStatus:
        """وضعیت فعلی - Type-safe enum"""
        return self._status
```

**مزایای Rich Domain Model**:
- ✅ Business logic encapsulated در domain objects
- ✅ Type-safe با استفاده از Value Objects و Enums
- ✅ Domain Events برای decoupling
- ✅ قابل تست به‌صورت مستقل

---

### 1.3 ❌ MAJOR: اختلاط Domain با Infrastructure

**مشکل**: کلاس‌های دامنه مستقیماً به Playwright وابسته هستند.

```python
# ❌ BAD: src/nemesis/collectors/console.py
from playwright.sync_api import ConsoleMessage, Page  # ⚠️ Framework dependency!

class ConsoleCollector(BaseCollector):
    """Collector مستقیماً به Playwright وابسته است"""

    def __init__(self, page: Page, filter_levels: list[str] | None = None):
        self.page = page  # ⚠️ نمی‌توان با Selenium جایگزین کرد
```

**چگونه باید باشد**:

```python
# ✅ GOOD: Dependency Inversion با Interface
from abc import ABC, abstractmethod
from typing import Protocol

class IBrowserPage(Protocol):
    """Interface برای Browser Page - Framework-agnostic"""

    def on_console_message(self, handler: Callable[[ConsoleMessage], None]) -> None:
        """Register console message handler"""
        ...

    def evaluate(self, script: str) -> Any:
        """Execute JavaScript"""
        ...

class ConsoleCollector:
    """Collector وابسته به abstraction است نه concrete framework"""

    def __init__(self, page: IBrowserPage, filter_levels: list[str] | None = None):
        self.page = page  # ✅ می‌توان هر پیاده‌سازی را inject کرد
```

**مزایا**:
- ✅ می‌توان Playwright را با Selenium یا Puppeteer جایگزین کرد
- ✅ تست با Mock آسان است
- ✅ Domain logic مستقل از Framework

---

### 1.4 ❌ MAJOR: عدم وجود Ubiquitous Language

**مشکل**: اصطلاحات در کدبیس inconsistent هستند.

**مثال‌ها**:
- "Scenario" vs "Test" (گاهی scenario، گاهی test)
- "Execution" vs "Test Suite" vs "Launch"
- Status values: `"PASSED"` vs `"passed"` vs `"Passed"`

```python
# فایل 1: data_model.py
status: str = "RUNNING"  # Uppercase

# فایل 2: hooks.py
status = "passed"  # Lowercase

# فایل 3: allure_builder.py
status = "Passed"  # Title case
```

**راه‌حل**:

```python
# ✅ GOOD: استفاده از Enum برای consistency
from enum import Enum

class ScenarioStatus(str, Enum):
    """Status values with Ubiquitous Language"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

    def is_terminal(self) -> bool:
        """آیا این status نهایی است؟"""
        return self in {ScenarioStatus.PASSED, ScenarioStatus.FAILED, ScenarioStatus.SKIPPED}
```

---

## 2️⃣ CLEAN ARCHITECTURE VIOLATIONS

### 2.1 ❌ CRITICAL: وابستگی معکوس (Dependency Direction Reversed)

**مشکل**: لایه Core به Infrastructure (Playwright) وابسته است - این کاملاً عکس Clean Architecture است!

```python
# ❌ BAD: src/nemesis/core/browser/browser_lifecycle.py
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)  # ⚠️ CORE به INFRASTRUCTURE وابسته است!

class BrowserLifecycle:
    """این کلاس در لایه Core است اما به Playwright وابسته!"""

    def __init__(self, config: ConfigLoader) -> None:
        self._playwright: Playwright | None = None  # ⚠️ Concrete type
        self._browser: Browser | None = None
```

**قانون Clean Architecture**:
> وابستگی‌ها باید از خارج به داخل باشند:
> Infrastructure → Application → Domain

**وضعیت فعلی**: Core → Infrastructure ❌

**راه‌حل**: Dependency Inversion

```python
# ✅ GOOD: src/nemesis/domain/ports/browser_driver.py
from abc import ABC, abstractmethod
from typing import Protocol

class IBrowserDriver(Protocol):
    """Port - Interface for browser automation (in Domain/Application layer)"""

    def launch(self, headless: bool, args: list[str]) -> "IBrowser":
        """Launch browser"""
        ...

    def close(self) -> None:
        """Close browser"""
        ...

class IBrowser(Protocol):
    """Interface for Browser instance"""

    def new_page(self) -> "IPage":
        ...

    def close(self) -> None:
        ...

# ✅ Adapter در لایه Infrastructure
# src/nemesis/infrastructure/browser/playwright_adapter.py
from playwright.sync_api import sync_playwright, Playwright, Browser

class PlaywrightBrowserDriver(IBrowserDriver):
    """Adapter - پیاده‌سازی IBrowserDriver با Playwright"""

    def __init__(self):
        self._playwright: Playwright | None = None

    def launch(self, headless: bool, args: list[str]) -> IBrowser:
        self._playwright = sync_playwright().start()
        browser = self._playwright.chromium.launch(headless=headless, args=args)
        return PlaywrightBrowserAdapter(browser)  # Wrap Playwright Browser
```

**مزایا**:
- ✅ Core مستقل از Playwright
- ✅ می‌توان SeleniumBrowserDriver یا PuppeteerBrowserDriver اضافه کرد
- ✅ تست Core بدون Playwright

---

### 2.2 ❌ CRITICAL: عدم وجود Abstraction Boundaries

**مشکل**: هیچ Interface یا Protocol برای تعریف مرزهای لایه‌ها وجود ندارد.

```python
# ❌ BAD: src/nemesis/reporting/management/reporter_manager.py
from nemesis.reporting.local import LocalReporter
from nemesis.reporting.reportportal import ReportPortalClient  # ⚠️ Concrete classes

class ReporterManager:
    def __init__(self, config, execution_manager, skip_rp_init=False):
        self.local_reporter = LocalReporter(...)  # ⚠️ Direct instantiation
        self.rp_client = ReportPortalClient(...)  # ⚠️ Direct instantiation
```

**راه‌حل**: Interface Segregation

```python
# ✅ GOOD: src/nemesis/domain/ports/reporter.py
from typing import Protocol, Any

class IReporter(Protocol):
    """Port - Interface برای Reporter"""

    def start_execution(self, execution_id: str) -> None: ...
    def end_execution(self, status: str) -> None: ...
    def start_scenario(self, scenario: Any) -> None: ...
    def end_scenario(self, scenario: Any, status: str) -> None: ...
    def attach_file(self, file_path: str, description: str) -> None: ...

# ✅ GOOD: Dependency Injection
class ReporterCoordinator:
    """Application layer - orchestrates reporters"""

    def __init__(self, reporters: list[IReporter]):  # ✅ Inject abstraction
        self.reporters = reporters

    def start_scenario(self, scenario: Any) -> None:
        for reporter in self.reporters:
            reporter.start_scenario(scenario)
```

**مزایا**:
- ✅ می‌توان reporter جدید اضافه کرد بدون تغییر ReporterCoordinator
- ✅ Mock کردن برای تست آسان
- ✅ Open/Closed Principle

---

### 2.3 ❌ CRITICAL: Framework Coupling

**مشکل**: منطق اصلی فریمورک شدیداً به Allure وابسته است.

```python
# ❌ BAD: src/nemesis/reporting/local/allure/allure_builder.py
from .allure_integration import AllureResultsGenerator
from .allure_cli_manager import AllureCLIManager  # ⚠️ Hard dependency on Allure

class AllureReportBuilder:
    """تولید گزارش مستقیماً به Allure وابسته است"""

    def __init__(self, execution_data, execution_path):
        self.cli_manager = AllureCLIManager()  # ⚠️ Concrete
```

**راه‌حل**: Adapter Pattern + Dependency Inversion

```python
# ✅ GOOD: src/nemesis/domain/ports/report_generator.py
class IReportGenerator(Protocol):
    """Port - Interface for report generation"""

    def generate_report(self, execution_data: ExecutionData, output_dir: Path) -> Path:
        """Generate HTML report and return path"""
        ...

# ✅ Adapter در لایه Infrastructure
class AllureReportGenerator(IReportGenerator):
    """Allure adapter"""

    def generate_report(self, execution_data: ExecutionData, output_dir: Path) -> Path:
        # Convert to Allure format and generate
        ...

class CustomHTMLReportGenerator(IReportGenerator):
    """پیاده‌سازی جایگزین با template engine"""

    def generate_report(self, execution_data: ExecutionData, output_dir: Path) -> Path:
        # Generate با Jinja2 یا custom HTML
        ...
```

---

### 2.4 ❌ MAJOR: Circular Dependencies

**مشکل**: وابستگی‌های دایره‌ای بین ماژول‌ها وجود دارد که با lazy import حل شده (anti-pattern).

```python
# ❌ BAD: src/nemesis/environment/hooks.py
if TYPE_CHECKING:
    from .environment_manager import EnvironmentManager  # ⚠️ Lazy import

def before_all(context):
    # Import at runtime to avoid circular dependency
    from .environment_manager import EnvironmentManager  # ⚠️ Anti-pattern
    _env_manager = EnvironmentManager()
```

**علت**: معماری اشتباه - hooks نباید به environment_manager وابسته باشد و برعکس.

**راه‌حل**: تفکیک صحیح لایه‌ها

```python
# ✅ GOOD: Dependency flow should be unidirectional
#
# CLI → Application Services → Domain
#         ↓
#    Infrastructure Adapters
```

---

## 3️⃣ SOLID VIOLATIONS

### 3.1 ❌ CRITICAL: نقض Single Responsibility Principle (SRP)

#### مثال 1: hooks.py - 352 خط، 7+ مسئولیت

**فایل**: `src/nemesis/environment/hooks.py`

**مسئولیت‌ها**:
1. مدیریت global state (`_env_manager`)
2. مقداردهی اولیه environment (before_all)
3. پاکسازی environment (after_all)
4. چرخه حیات feature (before/after_feature)
5. چرخه حیات scenario (before/after_scenario)
6. چرخه حیات step (before/after_step)
7. مدیریت browser crash

```python
# ❌ BAD: همه lifecycle hooks در یک فایل
_env_manager: Any = None  # Global state

def before_all(context): ...  # 60+ lines
def after_all(context): ...  # 50+ lines
def before_feature(context, feature): ...
def after_feature(context, feature): ...
def before_scenario(context, scenario): ...  # 80+ lines
def after_scenario(context, scenario): ...  # 70+ lines
def before_step(context, step): ...  # 40+ lines
def after_step(context, step): ...
```

**راه‌حل**: تفکیک مسئولیت‌ها

```python
# ✅ GOOD: src/nemesis/application/lifecycle/
├── execution_lifecycle.py       # before_all, after_all
├── feature_lifecycle.py         # before/after_feature
├── scenario_lifecycle.py        # before/after_scenario
├── step_lifecycle.py            # before/after_step
└── hooks.py                     # فقط integration با Behave

# hooks.py فقط delegate می‌کند:
from nemesis.application.lifecycle import (
    ExecutionLifecycle, FeatureLifecycle, ScenarioLifecycle, StepLifecycle
)

# Dependency Injection
execution_lifecycle = ExecutionLifecycle(config, browser_service, report_service)

def before_all(context):
    execution_lifecycle.setup(context)

def before_scenario(context, scenario):
    scenario_lifecycle.setup(context, scenario)
```

---

#### مثال 2: ReportManager - 291 خط، God Class

**فایل**: `src/nemesis/reporting/manager.py`

**مسئولیت‌ها**:
1. مقداردهی اولیه configuration
2. مدیریت execution
3. مدیریت reporters
4. مدیریت features
5. مدیریت scenarios
6. مدیریت steps
7. مدیریت attachments (screenshots, videos, traces, metrics)
8. Log message handling
9. Finalization
10. Backward compatibility properties

```python
# ❌ BAD: God class
class ReportManager:
    def __init__(self, context=None, skip_rp_init=False):
        self.config = ConfigLoader()
        self.execution_manager = ExecutionManager(...)
        self.reporter_manager = ReporterManager(...)
        self.feature_manager = FeatureManager(...)
        self.scenario_manager = ScenarioManager(...)
        self.step_manager = StepManager(...)
        self.attachment_manager = AttachmentManager(...)
        self.finalization_manager = FinalizationManager(...)
        # ⚠️ 8 dependencies!
```

**راه‌حل**: تفکیک به Coordinators کوچک‌تر

```python
# ✅ GOOD: تفکیک مسئولیت‌ها
# src/nemesis/application/services/

class ExecutionCoordinator:
    """مسئول execution lifecycle"""
    def __init__(self, execution_service: IExecutionService):
        self.execution_service = execution_service

    def start_execution(self) -> ExecutionId: ...
    def end_execution(self) -> None: ...

class ReportingCoordinator:
    """مسئول هماهنگی reporters"""
    def __init__(self, reporters: list[IReporter]):
        self.reporters = reporters

    def start_scenario(self, scenario: Scenario) -> None:
        for reporter in self.reporters:
            reporter.start_scenario(scenario)

class AttachmentCoordinator:
    """مسئول attachment handling"""
    def __init__(self, attachment_handlers: list[IAttachmentHandler]):
        self.handlers = attachment_handlers

    def attach_screenshot(self, screenshot: bytes, name: str) -> None: ...
```

---

### 3.2 ❌ MAJOR: نقض Dependency Inversion Principle (DIP)

**مشکل**: همه‌جا concrete classes استفاده شده، نه abstractions.

```python
# ❌ BAD: وابستگی به concrete class
from nemesis.reporting.local import LocalReporter

class ReporterManager:
    def __init__(self):
        self.local_reporter = LocalReporter(...)  # ⚠️ Concrete dependency
```

**راه‌حل**: Depend on abstractions

```python
# ✅ GOOD: وابستگی به abstraction
from nemesis.domain.ports import IReporter

class ReporterCoordinator:
    def __init__(self, reporters: list[IReporter]):  # ✅ Abstraction
        self.reporters = reporters

# Dependency injection at composition root:
reporters = [
    LocalReporter(...),
    ReportPortalReporter(...),
]
coordinator = ReporterCoordinator(reporters)
```

---

### 3.3 ❌ MAJOR: نقض Open/Closed Principle (OCP)

**مشکل**: اضافه کردن feature جدید نیازمند تغییر کد موجود است.

```python
# ❌ BAD: src/nemesis/cli/commands/run.py
@click.command()
@click.option("--tags", ...)
@click.option("--feature", ...)
@click.option("--env", ...)
@click.option("--report", ...)
@click.option("--parallel", ...)
@click.option("--headless", ...)
# ⚠️ اضافه کردن option جدید = تغییر signature

def run_command(tags, feature, env, report, parallel, headless, ...):
    # 143 lines of logic
```

**راه‌حل**: استفاده از Configuration Object + Plugin Architecture

```python
# ✅ GOOD: Extensible architecture
@dataclass
class TestRunConfig:
    """Configuration object"""
    tags: list[str]
    features: list[str]
    environment: str
    reporters: list[str]
    parallel_workers: int
    headless: bool
    plugins: list[ITestPlugin]  # ✅ Plugin support

class TestRunner:
    def __init__(self, config: TestRunConfig):
        self.config = config

    def run(self) -> TestResult:
        # Execute plugins
        for plugin in self.config.plugins:
            plugin.before_run(self.config)

        # Run tests
        result = self._execute_tests()

        # Execute plugins
        for plugin in self.config.plugins:
            plugin.after_run(result)

        return result
```

---

### 3.4 ❌ MINOR: نقض Liskov Substitution Principle (LSP)

**مشکل**: `BrowserManager` به private attributes وابستگی‌هایش دسترسی دارد.

```python
# ❌ BAD: Breaking encapsulation
def _cleanup_resources(self) -> None:
    self.cleanup.cleanup_resources(
        self.lifecycle._playwright,  # ⚠️ Accessing private!
        self.lifecycle._browser,
        self.lifecycle._context,
        self.lifecycle._page
    )
```

**راه‌حل**: Expose only public interface

```python
# ✅ GOOD: Use public methods
class BrowserLifecycle:
    def cleanup_all(self) -> None:
        """Public cleanup method"""
        self._cleanup_playwright()
        self._cleanup_browser()
        # Internal private methods
```

---

## 4️⃣ CODE SMELLS & TECHNICAL DEBT

### 4.1 🟡 Primitive Obsession

**مشکل**: استفاده از types primitive به جای Value Objects.

```python
# ❌ BAD: execution_id به عنوان string
execution_id: str = "exec_20250416_123456"

# ❌ BAD: status به عنوان string
status: str = "PASSED"

# ❌ BAD: duration به عنوان float
duration: float = 15.3
```

**راه‌حل**: Value Objects

```python
# ✅ GOOD: src/nemesis/domain/value_objects/

from dataclasses import dataclass
from datetime import datetime
from typing import NewType

@dataclass(frozen=True)
class ExecutionId:
    """Value object for execution ID"""
    value: str

    def __post_init__(self):
        if not self.value.startswith("exec_"):
            raise ValueError("ExecutionId must start with 'exec_'")

    def __str__(self) -> str:
        return self.value

class ScenarioStatus(str, Enum):
    """Type-safe status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

@dataclass(frozen=True)
class Duration:
    """Value object for duration"""
    seconds: float

    def to_milliseconds(self) -> int:
        return int(self.seconds * 1000)

    def __str__(self) -> str:
        return f"{self.seconds:.2f}s"
```

---

### 4.2 🟡 Long Methods

**مشکل**: متدهای بیش از 50 خط.

```python
# ❌ BAD: _cleanup_resources - 112 lines!
def _cleanup_resources(self) -> None:
    # Lines 1-20: Video directory handling
    # Lines 21-40: Dispose collectors
    # Lines 41-60: HAR-safe context closure
    # Lines 61-80: Browser closure with retry
    # Lines 81-100: Playwright stop
    # Lines 101-112: Reset state
```

**راه‌حل**: Extract methods

```python
# ✅ GOOD: تفکیک به متدهای کوچک‌تر
def cleanup_resources(self) -> None:
    """Cleanup all browser resources"""
    self._save_video_path()
    self._dispose_collectors()
    self._close_context()
    self._close_browser()
    self._stop_playwright()
    self._reset_state()

def _save_video_path(self) -> None:
    """Save video directory path before closing context"""
    # 10 lines

def _dispose_collectors(self) -> None:
    """Dispose all collectors"""
    # 10 lines

# هر متد فقط یک کار انجام می‌دهد
```

---

### 4.3 🟡 Feature Envy

**مشکل**: ReportManager به internals مدیران دیگر دسترسی دارد.

```python
# ❌ BAD: Feature envy
def start_scenario(self, scenario):
    # Reaching into reporter_manager
    if self.reporter_manager.get_local_reporter():
        self.reporter_manager.get_local_reporter().start_scenario(scenario)

    # Then delegates
    self.scenario_manager.start_scenario(scenario)
```

**راه‌حل**: Tell, Don't Ask

```python
# ✅ GOOD: Delegate, don't interrogate
def start_scenario(self, scenario):
    self.scenario_coordinator.start(scenario)
    # Coordinator internally manages all reporters
```

---

### 4.4 🟡 Shotgun Surgery

**مشکل**: تغییر یک feature نیازمند تغییر در چندین فایل است.

**مثال**: اضافه کردن status جدید `"BLOCKED"`:

```
باید در 5+ فایل تغییر ایجاد کرد:
1. data_model.py
2. hooks.py
3. scenario_helpers.py
4. LocalReporter
5. ReportPortalClient
```

**راه‌حل**: استفاده از Enum و Single Source of Truth

```python
# ✅ GOOD: فقط یک جا تعریف می‌شود
class ScenarioStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"  # ✅ فقط اینجا اضافه می‌شود
```

---

### 4.5 🟡 Duplicated Code

**مشکل**: الگوهای error handling تکراری.

```python
# تکرار در 50+ جا:
except (KeyboardInterrupt, SystemExit):
    raise
except (AttributeError, RuntimeError) as e:
    self.logger.error(f"Error: {e}", traceback=traceback.format_exc())
except Exception as e:
    self.logger.error(f"Error: {e}", traceback=traceback.format_exc())
```

**راه‌حل**: Decorator

```python
# ✅ GOOD: src/nemesis/utils/decorators/error_handling.py
def handle_errors(logger: Logger, reraise: bool = False):
    """Decorator برای error handling یکسان"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", traceback=True)
                if reraise:
                    raise
        return wrapper
    return decorator

# Usage:
@handle_errors(logger)
def my_method(self):
    ...
```

---

### 4.6 🟡 Comments Explaining Code

**مشکل**: کدی که نیاز به comment دارد = کد پیچیده.

```python
# ❌ BAD: Comments explaining what code does
# Step 1: Generate Allure results JSON files
self.logger.info("Generating Allure results JSON files...")
results_generator = AllureResultsGenerator(...)
results_generator.generate_from_execution_data(self.execution_data)

# Step 1.5: Generate environment.json and executor.json
self._generate_environment_files()

# Step 2: Try to use Allure CLI to generate HTML
if self._try_allure_cli():
    return
```

**راه‌حل**: Self-documenting code با نام‌های واضح

```python
# ✅ GOOD: نام‌های روشن، نه comment
def generate_report(self) -> None:
    self._generate_allure_json_results()
    self._generate_allure_metadata_files()
    self._generate_html_with_allure_cli_or_fallback()

def _generate_allure_json_results(self) -> None:
    """Generate Allure results JSON files from execution data"""
    results_generator = AllureResultsGenerator(...)
    results_generator.generate_from_execution_data(self.execution_data)
```

---

## 5️⃣ LOGGING ARCHITECTURE ANALYSIS

### وضعیت فعلی لاگینگ: 🟡 نیازمند بهبود

**نقاط قوت**:
- ✅ Structured logging موجود است
- ✅ Context manager برای correlation IDs
- ✅ Severity mapping پایه‌ای
- ✅ Multi-channel shipping (local file)

**نقایص شناسایی‌شده**:

#### 1. فقدان SigNoz Integration واقعی

```python
# ❌ موجود: فقط LocalChannel
# src/nemesis/core/logging/shipping/channels/local.py

# ✅ مورد نیاز: SigNozChannel
class SigNozChannel(IShippingChannel):
    """Ship logs to SigNoz observability platform"""

    def __init__(self, config: SigNozConfig):
        self.endpoint = config.endpoint
        self.service_name = config.service_name
        self.batch_size = config.batch_size

    def ship(self, logs: list[LogEntry]) -> bool:
        # Batch shipping با retry logic
        for batch in self._create_batches(logs):
            self._ship_batch_with_retry(batch)
```

#### 2. Context Propagation ناقص

```python
# ❌ BAD: ConsoleCollector بدون correlation_id
log_entry = {
    "type": msg_type,
    "text": text,
    "timestamp": self._get_timestamp(),
    # ⚠️ فاقد correlation_id و execution_id
}

# ✅ GOOD: باید همه collectors context کامل داشته باشند
log_entry = {
    "timestamp": time.time(),
    "level": "ERROR",
    "message": f"Console {msg_type}: {text}",
    "correlation_id": context_manager.get_correlation_id(),
    "execution_id": context_manager.get_execution_id(),
    "context": {
        "module": "console_collector",
        "console_type": msg_type,
        "location": location
    },
    "service_name": "nemesis-framework",
}
```

#### 3. Service Name Conflict

```python
# مشکل: دو service name مختلف در SigNoz
# Framework logs: service_name = "nemesis-framework"
# Test logs: service_name = "saucedemo-automation"

# ✅ راه‌حل: تفکیک واضح
class LoggingConfig:
    framework_service_name: str = "nemesis-framework"
    test_service_name: str  # از پروژه test می‌آید
```

---

## 6️⃣ CLI OUTPUT ANALYSIS

### وضعیت فعلی CLI: 🟡 نیازمند بهبود

**نقاط قوت**:
- ✅ استفاده از Rich برای output زیبا
- ✅ Color-coded messages
- ✅ Table display

**نقایص** (مقایسه با Cypress):

#### Cypress Output:
```
  Running:  login.feature                                          (1 of 3)

  User Authentication
    ✓ Successful login with standard user (2.5s)
    ✓ Login fails with invalid credentials (1.2s)
    ✗ Login fails with locked user
      1) Expected URL to contain "/inventory"

  2 passing (3.7s)
  1 failing

  1) User Authentication > Login fails with locked user:
     AssertionError: Expected URL to contain "/inventory"
      at LoginPage.verify_redirect (pages/login_page.py:45)
```

#### Nemesis Current Output:
```
Feature: User Authentication
  Scenario: Successful login
    ✓ Given I am on login page
    ✓ When I enter credentials
    ✓ Then I should see inventory
```

**پیشنهاد بهبود**:

```python
# ✅ GOOD: Cypress-like output
class CypressStyleReporter:
    """CLI reporter با سبک Cypress"""

    def print_feature_header(self, feature: Feature):
        """نمایش feature با progress"""
        console.print(f"\n  Running: {feature.name}.feature", style="cyan")
        console.print(f"  ({feature.index} of {total_features})\n")

    def print_scenario_result(self, scenario: Scenario):
        """نمایش نتیجه scenario"""
        icon = "✓" if scenario.passed else "✗"
        color = "green" if scenario.passed else "red"
        console.print(f"    {icon} {scenario.name} ({scenario.duration}s)", style=color)

    def print_summary(self, execution: Execution):
        """خلاصه نهایی"""
        console.print(f"\n  {execution.passed_count} passing ({execution.duration}s)", style="green")
        if execution.failed_count > 0:
            console.print(f"  {execution.failed_count} failing", style="red")
```

---

## 7️⃣ HTML REPORTING REMOVAL

### مشکل: فریمورک نباید HTML تولید کند

**فایل‌های مرتبط با HTML reporting**:
1. `src/nemesis/reporting/local/reporter.py` - LocalReporter
2. `src/nemesis/reporting/local/allure/*` - تمام Allure integration
3. `src/nemesis/cli/commands/open.py` - دستور `nemesis open`

**پیشنهاد**:

```
✅ حفظ: JSON results generation
❌ حذف: HTML report generation
❌ حذف: Allure CLI integration
❌ حذف: allure-report directory creation
```

**راه‌حل**: فریمورک فقط JSON تولید می‌کند، پروژه test تصمیم می‌گیرد چطور مصرف کند.

```python
# ✅ GOOD: فقط JSON
class ExecutionReporter:
    """تولید گزارش JSON ساده"""

    def generate_report(self, execution: Execution) -> Path:
        """Generate JSON report"""
        report_path = self.output_dir / "execution_report.json"
        with open(report_path, "w") as f:
            json.dump(execution.to_dict(), f, indent=2)
        return report_path
```

**مزایا**:
- ✅ Framework ساده‌تر و سبک‌تر
- ✅ پروژه test می‌تواند از هر report generator استفاده کند
- ✅ جدایی مسئولیت‌ها

---

## 8️⃣ PROPOSED ARCHITECTURE - معماری پیشنهادی

### ساختار پیشنهادی بر اساس Clean Architecture + DDD:

```
Nemesis/
├── src/nemesis/
│   ├── domain/                          # 🔵 DOMAIN LAYER
│   │   ├── entities/                    # Entities با behavior
│   │   │   ├── execution.py
│   │   │   ├── scenario.py
│   │   │   └── step.py
│   │   ├── value_objects/               # Value Objects
│   │   │   ├── execution_id.py
│   │   │   ├── scenario_status.py
│   │   │   └── duration.py
│   │   ├── events/                      # Domain Events
│   │   │   ├── scenario_started.py
│   │   │   ├── scenario_completed.py
│   │   │   └── execution_failed.py
│   │   ├── services/                    # Domain Services
│   │   │   └── status_calculator.py
│   │   └── ports/                       # Interfaces (Ports)
│   │       ├── browser_driver.py        # IBrowserDriver
│   │       ├── reporter.py              # IReporter
│   │       └── collector.py             # ICollector
│   │
│   ├── application/                     # 🟢 APPLICATION LAYER
│   │   ├── use_cases/                   # Use Cases
│   │   │   ├── execute_test_scenario.py
│   │   │   ├── generate_test_report.py
│   │   │   └── collect_performance_metrics.py
│   │   ├── services/                    # Application Services
│   │   │   ├── execution_coordinator.py
│   │   │   ├── reporting_coordinator.py
│   │   │   └── attachment_coordinator.py
│   │   └── dto/                         # Data Transfer Objects
│   │       ├── scenario_dto.py
│   │       └── execution_dto.py
│   │
│   ├── infrastructure/                  # 🟠 INFRASTRUCTURE LAYER
│   │   ├── browser/                     # Browser Adapters
│   │   │   ├── playwright_adapter.py    # PlaywrightBrowserDriver
│   │   │   └── selenium_adapter.py      # (future)
│   │   ├── reporting/                   # Reporter Adapters
│   │   │   ├── json_reporter.py         # JSONReporter
│   │   │   ├── reportportal_adapter.py  # ReportPortalReporter
│   │   │   └── console_reporter.py      # CypressStyleReporter
│   │   ├── logging/                     # Logging Infrastructure
│   │   │   ├── signoz_shipper.py        # SigNozChannel
│   │   │   └── file_shipper.py          # LocalChannel
│   │   ├── collectors/                  # Collector Implementations
│   │   │   ├── console_collector.py
│   │   │   ├── network_collector.py
│   │   │   └── performance_collector.py
│   │   └── persistence/                 # Data persistence
│   │       └── json_repository.py
│   │
│   ├── cli/                             # 🔴 INTERFACE LAYER
│   │   ├── commands/
│   │   │   ├── run.py
│   │   │   ├── init.py
│   │   │   └── validate.py
│   │   ├── ui/
│   │   │   └── cypress_style_output.py
│   │   └── main.py
│   │
│   └── composition_root.py              # Dependency Injection setup
```

### Dependency Flow (Clean Architecture):

```
CLI → Application Use Cases → Domain
         ↓
   Infrastructure Adapters
```

**قوانین**:
- ✅ Domain: هیچ وابستگی به خارج ندارد
- ✅ Application: فقط به Domain وابسته است
- ✅ Infrastructure: به Domain و Application وابسته (پیاده‌سازی Ports)
- ✅ CLI: به همه وابسته (composition root)

---

## 9️⃣ REFACTORING ROADMAP - نقشه راه بازسازی

### Phase 1: ایجاد Domain Layer (اولویت بالا) ⚠️

**هدف**: تعریف مدل دامنه با business logic.

**Tasks**:
1. ✅ ایجاد Entities: `Execution`, `Scenario`, `Step`
2. ✅ ایجاد Value Objects: `ExecutionId`, `ScenarioStatus`, `Duration`
3. ✅ ایجاد Domain Events: `ScenarioStarted`, `ScenarioCompleted`
4. ✅ تعریف Ports (Interfaces): `IBrowserDriver`, `IReporter`, `ICollector`
5. ✅ Domain Services: `StatusCalculator`

**زمان تخمینی**: 2-3 روز

---

### Phase 2: Dependency Inversion (اولویت بالا) ⚠️

**هدف**: جداسازی Core از Infrastructure.

**Tasks**:
1. ✅ ایجاد `IBrowserDriver` interface
2. ✅ ایجاد `PlaywrightBrowserDriver` adapter
3. ✅ Refactor `BrowserLifecycle` به استفاده از interface
4. ✅ ایجاد `IReporter` interface
5. ✅ Refactor `ReporterManager` به استفاده از DI

**زمان تخمینی**: 3-4 روز

---

### Phase 3: تفکیک God Classes (اولویت متوسط) 🟡

**هدف**: شکستن God Classes به کلاس‌های کوچک‌تر.

**Tasks**:
1. ✅ Split `ReportManager` به:
   - `ExecutionCoordinator`
   - `ReportingCoordinator`
   - `AttachmentCoordinator`
2. ✅ Split `hooks.py` به:
   - `ExecutionLifecycle`
   - `FeatureLifecycle`
   - `ScenarioLifecycle`
   - `StepLifecycle`
3. ✅ Simplify `EnvironmentManager`

**زمان تخمینی**: 2-3 روز

---

### Phase 4: حذف HTML Reporting (اولویت متوسط) 🟡

**Tasks**:
1. ✅ حذف `reporting/local/allure/` directory
2. ✅ Refactor `LocalReporter` به `JSONReporter`
3. ✅ حذف `cli/commands/open.py`
4. ✅ Update documentation

**زمان تخمینی**: 1 روز

---

### Phase 5: بهبود Logging (اولویت متوسط) 🟡

**Tasks**:
1. ✅ پیاده‌سازی `SigNozChannel`
2. ✅ اضافه کردن correlation_id به همه collectors
3. ✅ تفکیک service_name برای framework و test
4. ✅ Batch shipping با retry logic

**زمان تخمینی**: 2 روز

---

### Phase 6: بهبود CLI Output (اولویت پایین) 🟢

**Tasks**:
1. ✅ پیاده‌سازی `CypressStyleReporter`
2. ✅ بهبود progress display
3. ✅ خلاصه نهایی با statistics

**زمان تخمینی**: 1-2 روز

---

### Phase 7: حذف Technical Debt (اولویت پایین) 🟢

**Tasks**:
1. ✅ Refactor long methods
2. ✅ حذف duplicated code
3. ✅ Error handling decorators
4. ✅ Self-documenting code (حذف comments غیرضروری)

**زمان تخمینی**: 2-3 روز

---

## 🔟 MIGRATION GUIDE - راهنمای مهاجرت

### برای پروژه saucedemo-automation:

#### Before (قبل از refactoring):

```python
# features/environment.py
from nemesis.environment import (
    before_all, after_all, before_feature, after_feature,
    before_scenario, after_scenario, before_step, after_step
)
```

#### After (بعد از refactoring):

```python
# features/environment.py
from nemesis.application.lifecycle import Lifecycle

lifecycle = Lifecycle()

def before_all(context):
    lifecycle.execution.setup(context)

def after_all(context):
    lifecycle.execution.teardown(context)

def before_scenario(context, scenario):
    lifecycle.scenario.setup(context, scenario)

def after_scenario(context, scenario):
    lifecycle.scenario.teardown(context, scenario)
```

**Breaking Changes**:
- ✅ Simplified hook imports
- ✅ Explicit lifecycle management
- ✅ Better control over framework behavior

---

## 1️⃣1️⃣ SUMMARY & RECOMMENDATIONS

### خلاصه مشکلات اصلی:

| مشکل | شدت | اولویت رفع |
|------|-----|-----------|
| عدم Domain Model | 🔴 CRITICAL | HIGH |
| Dependency Direction | 🔴 CRITICAL | HIGH |
| God Classes | 🔴 CRITICAL | MEDIUM |
| Primitive Obsession | 🟡 MAJOR | MEDIUM |
| HTML Reporting | 🟡 MAJOR | MEDIUM |
| Logging Gaps | 🟡 MAJOR | MEDIUM |
| CLI Output | 🟢 MINOR | LOW |

---

### توصیه نهایی:

> **این فریمورک از نظر functional کامل است اما از نظر architectural نیازمند بازسازی اساسی دارد.**

**مزایای بازسازی**:
- ✅ **Maintainability**: کد قابل نگهداری و فهم
- ✅ **Testability**: تست واحد آسان
- ✅ **Flexibility**: جایگزینی Playwright/Allure/ReportPortal
- ✅ **Extensibility**: افزودن features بدون تغییر کد موجود
- ✅ **Professional Grade**: معماری حرفه‌ای production-ready

**هزینه**:
- ⏱️ **زمان**: 2-3 هفته refactoring
- 🧪 **تست**: نیاز به regression testing کامل
- 📚 **مستندسازی**: update documentation و migration guide

**نتیجه**:
بدون refactoring، این فریمورک به technical debt بیشتری دچار خواهد شد و نگهداری آن سخت‌تر می‌شود.

با refactoring، یک فریمورک production-grade با معماری تمیز خواهید داشت که برای سال‌ها قابل نگهداری و توسعه است.

---

**پایان گزارش**


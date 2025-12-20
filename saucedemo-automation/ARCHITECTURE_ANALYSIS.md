# تحلیل معماری - مشکل environment.py

## 🔍 تحلیل بر اساس Clean Architecture, DDD, و SOLID

### مشکل اصلی

**دو سیستم hooks با هم تداخل دارند:**

1. **Framework Hooks** (در `nemesis.infrastructure.environment.hooks`):
   - از `EnvironmentCoordinator` استفاده می‌کند
   - مدیریت کامل lifecycle را انجام می‌دهد
   - با ConfigLoader و تمام زیرسیستم‌ها یکپارچه است

2. **Custom Environment** (در `saucedemo-automation/features/environment.py`):
   - یک نسخه سفارشی از Clean Architecture
   - از `ExecutionCoordinator` و `ScenarioCoordinator` استفاده می‌کند
   - با framework hooks سازگار نیست

### مشکلات شناسایی شده

#### 1. **Violation of Dependency Inversion Principle (SOLID)**

```python
# ❌ مشکل: environment.py مستقیماً از Application Layer استفاده می‌کند
from nemesis.application.services import ExecutionCoordinator, ScenarioCoordinator

# ✅ باید: از Infrastructure Layer (hooks) استفاده کند
from nemesis.infrastructure.environment.hooks import before_all, after_all
```

**تحلیل**: 
- Test project نباید مستقیماً از Application Layer استفاده کند
- باید از Infrastructure Layer (hooks) استفاده کند که خودش Application Layer را مدیریت می‌کند

#### 2. **Violation of Single Responsibility Principle (SOLID)**

`environment.py` دو مسئولیت دارد:
- مدیریت lifecycle (که باید توسط framework انجام شود)
- Dependency Injection (که می‌تواند در hooks framework انجام شود)

#### 3. **Violation of Clean Architecture Layers**

```
┌─────────────────────────────────────┐
│   Test Project (saucedemo)         │
│   ❌ environment.py                │  ← نباید اینجا باشد!
│   ❌ مستقیماً از Application Layer │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Framework Infrastructure         │
│   ✅ hooks.py                      │  ← باید اینجا باشد
│   ✅ EnvironmentCoordinator        │
└─────────────────────────────────────┘
```

**مشکل**: Test project نباید lifecycle management را خودش انجام دهد.

#### 4. **Missing Logger Dependency**

```python
# ❌ مشکل: ExecutionCoordinator نیاز به logger دارد
self.execution_coordinator = ExecutionCoordinator(
    reporters=self.reporters,
    output_dir=self.output_dir
    # ❌ logger missing!
)
```

**تحلیل**: 
- `ExecutionCoordinator` نیاز به `ILogger` دارد (Dependency Injection)
- `environment.py` این dependency را inject نمی‌کند

#### 5. **Duplicate Hooks Definition**

دو set hooks وجود دارد:
- Framework hooks در `nemesis.infrastructure.environment.hooks`
- Custom hooks در `features/environment.py`

**مشکل**: Behave فقط یک set hooks را اجرا می‌کند (طبق `behave.ini`)

### راه حل صحیح بر اساس Clean Architecture

#### گزینه 1: استفاده از Framework Hooks (توصیه می‌شود)

**اصلاح `behave.ini`:**
```ini
[behave]
environment_file = nemesis.infrastructure.environment.hooks
```

**مزایا:**
- ✅ از Clean Architecture پیروی می‌کند
- ✅ Framework lifecycle management را مدیریت می‌کند
- ✅ با تمام زیرسیستم‌ها یکپارچه است
- ✅ ConfigLoader را استفاده می‌کند

**معایب:**
- نیاز به تنظیمات اضافی در config files

#### گزینه 2: Import Framework Hooks در environment.py

**اصلاح `environment.py`:**
```python
# Import framework hooks
from nemesis.infrastructure.environment.hooks import (
    before_all as framework_before_all,
    after_all as framework_after_all,
    before_scenario as framework_before_scenario,
    after_scenario as framework_after_scenario,
    before_step as framework_before_step,
    after_step as framework_after_step
)

# Delegate to framework hooks
def before_all(context):
    framework_before_all(context)
    # Custom logic if needed

def after_all(context):
    framework_after_all(context)
    # Custom logic if needed
```

**مزایا:**
- ✅ از framework hooks استفاده می‌کند
- ✅ امکان اضافه کردن custom logic دارد

**معایب:**
- هنوز یک layer اضافی است

#### گزینه 3: حذف environment.py و استفاده مستقیم از Framework

**حذف `environment.py` و تغییر `behave.ini`:**
```ini
[behave]
environment_file = nemesis.infrastructure.environment.hooks
```

**مزایا:**
- ✅ ساده‌ترین راه حل
- ✅ از Clean Architecture پیروی می‌کند
- ✅ هیچ duplicate code ندارد

**معایب:**
- نیاز به تنظیمات در config files

### توصیه نهایی

**گزینه 3** بهترین است چون:
1. ✅ از Clean Architecture پیروی می‌کند
2. ✅ Framework lifecycle management را مدیریت می‌کند
3. ✅ هیچ duplicate code ندارد
4. ✅ با تمام زیرسیستم‌ها یکپارچه است

### مراحل پیاده‌سازی

1. **حذف `features/environment.py`**
2. **تغییر `behave.ini`:**
   ```ini
   environment_file = nemesis.infrastructure.environment.hooks
   ```
3. **تنظیم config files** (playwright.yaml, reporting.yaml, etc.)
4. **تست کردن**

### نکات مهم

- Framework hooks از `EnvironmentCoordinator` استفاده می‌کند که خودش:
  - BrowserEnvironment را مدیریت می‌کند
  - ReportingEnvironment را مدیریت می‌کند
  - LoggerEnvironment را مدیریت می‌کند
  - ConfigLoader را استفاده می‌کند

- Test project فقط باید:
  - Feature files را تعریف کند
  - Step definitions را بنویسد
  - Config files را تنظیم کند

- Lifecycle management باید توسط framework انجام شود نه test project.


# ReportPortal Libraries - توضیحات کامل

## 📚 کتابخانه‌های استفاده شده

### 1. `reportportal-client` (کتابخانه اصلی) ✅ **استفاده می‌شود**

**نسخه**: `>=5.5.0`

**استفاده در کد**:
```python
from reportportal_client import RPClient
```

**فایل‌های استفاده کننده**:
- `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_client_base.py` (خط 6)
- `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_launch_coordinator.py` (خط 11)
- `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_feature_handler.py` (خط 6)
- `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_test_handler.py` (خط 7)
- و سایر فایل‌های reporting

**توضیح**:
- این کتابخانه **کتابخانه اصلی** ReportPortal برای Python است
- کلاس اصلی: `RPClient` - برای ارتباط با ReportPortal API
- قابلیت‌ها:
  - ایجاد و مدیریت Launch
  - ایجاد Test Items (Feature, Scenario, Step)
  - ارسال Logs و Attachments
  - Async Queue برای performance
  - `terminate()` برای flush کردن queue

**مثال استفاده**:
```python
from reportportal_client import RPClient

client = RPClient(
    endpoint="http://localhost:8080",
    project="my_project",
    api_key="my_api_key",
    verify_ssl=True
)

# Start launch
launch_id = client.start_launch(
    name="My Launch",
    start_time=timestamp,
    description="Launch description"
)

# Start test item
test_id = client.start_test_item(
    name="My Test",
    start_time=timestamp,
    item_type="TEST",
    launch_uuid=launch_id
)

# Finish test item
client.finish_test_item(
    item_id=test_id,
    end_time=timestamp,
    status="PASSED",
    launch_uuid=launch_id
)

# Finish launch
client.finish_launch(
    end_time=timestamp,
    status="FINISHED"
)

# CRITICAL: Flush async queue
client.terminate()
```

---

### 2. `behave-reportportal` ⚠️ **در requirements هست اما استفاده نمی‌شود**

**نسخه**: `>=5.0.0`

**وضعیت**: 
- ✅ در `requirements.txt` و `pyproject.toml` موجود است
- ❌ در کد استفاده **نشده** است

**توضیح**:
- `behave-reportportal` یک **agent** است که به صورت خودکار با Behave hooks کار می‌کند
- این agent به صورت **monolithic** کار می‌کند و تمام lifecycle را خودش مدیریت می‌کند
- در Nemesis Framework، ما **custom implementation** داریم که از `reportportal-client` مستقیماً استفاده می‌کند

**چرا استفاده نمی‌شود؟**
1. **Clean Architecture**: Nemesis از Clean Architecture استفاده می‌کند و نمی‌خواهد به agent وابسته باشد
2. **Custom Control**: کنترل کامل روی lifecycle و reporting
3. **Multi-Reporter**: پشتیبانی از Local HTML + ReportPortal همزمان
4. **BDD-Optimized**: فرمت‌بندی مخصوص BDD (Feature, Scenario, Step)
5. **Error Resilience**: Tests ادامه می‌یابند حتی اگر ReportPortal fail شود

---

## 🤔 behave-reportportal (Agent) چیست؟

### تعریف:
`behave-reportportal` یک **agent** است که به صورت خودکار با Behave framework کار می‌کند و تست‌ها را به ReportPortal ارسال می‌کند.

### نحوه کار:
1. **Configuration**: از `behave.ini` یا `reportportal.yaml` تنظیمات را می‌خواند
2. **Auto-Integration**: به صورت خودکار با Behave hooks integrate می‌شود
3. **Lifecycle Management**: تمام lifecycle (launch, feature, scenario, step) را خودش مدیریت می‌کند
4. **Automatic Reporting**: به صورت خودکار همه چیز را به ReportPortal ارسال می‌کند

### مثال استفاده (اگر از agent استفاده می‌شد):
```python
# behave.ini
[report_portal]
rp_enabled = True
rp_endpoint = http://localhost:8080
rp_project = my_project
rp_api_key = my_api_key
rp_launch = My Launch
rp_launch_description = My test launch
rp_log_layout = NESTED
```

```python
# features/environment.py
from behave_reportportal.behave_agent import BehaveAgent

agent = BehaveAgent()
# Agent به صورت خودکار با hooks کار می‌کند
```

### تفاوت با Implementation فعلی:

| ویژگی | behave-reportportal (Agent) | Nemesis Implementation |
|-------|------------------------------|------------------------|
| **Architecture** | Monolithic (Singleton) | Clean Architecture (Layered) |
| **Control** | Automatic (Limited Control) | Full Control |
| **Customization** | Limited | Full Customization |
| **Multi-Reporter** | ❌ Only ReportPortal | ✅ Local + ReportPortal |
| **Error Handling** | ❌ Tests fail if RP fails | ✅ Tests continue |
| **BDD Formatting** | Basic | Advanced (BDD-optimized) |
| **Lifecycle Management** | Automatic | Manual (Full Control) |

---

## 📦 Dependency Tree

```
nemesis-automation
├── behave>=1.2.6                    # BDD Framework
├── playwright>=1.40.0               # Browser Automation
├── reportportal-client>=5.5.0        # ✅ استفاده می‌شود - کتابخانه اصلی
├── behave-reportportal>=5.0.0       # ⚠️ در requirements هست اما استفاده نمی‌شود
├── pyyaml>=6.0                       # Configuration
├── rich>=13.7.0                      # Console Output
├── click>=8.1.7                      # CLI
├── pydantic>=2.5.0                   # Data Validation
├── pydantic-settings>=2.1.0          # Settings Management
├── requests>=2.32.3                  # HTTP Requests (برای direct API calls)
└── urllib3>=1.21.1                   # HTTP Library
```

---

## 🔍 چرا `behave-reportportal` در requirements هست؟

**احتمالات**:
1. **Future Use**: ممکن است در آینده استفاده شود
2. **Dependency**: ممکن است dependency دیگری باشد
3. **Reference**: برای reference و comparison
4. **Legacy**: ممکن است از قبل بوده و حذف نشده

**توصیه**: 
- اگر استفاده نمی‌شود، می‌توان از requirements حذف کرد
- یا می‌توان در documentation توضیح داد که چرا استفاده نمی‌شود

---

## 📝 خلاصه

### کتابخانه‌های استفاده شده:
1. ✅ **`reportportal-client`** - کتابخانه اصلی، استفاده می‌شود
2. ⚠️ **`behave-reportportal`** - در requirements هست اما استفاده نمی‌شود

### دلیل استفاده از `reportportal-client` به جای `behave-reportportal`:
1. **Clean Architecture** - کنترل کامل روی architecture
2. **Custom Implementation** - فرمت‌بندی مخصوص BDD
3. **Multi-Reporter** - پشتیبانی از Local + ReportPortal
4. **Error Resilience** - Tests ادامه می‌یابند حتی اگر RP fail شود
5. **Full Control** - کنترل کامل روی lifecycle

---

**تاریخ**: 2025-12-19


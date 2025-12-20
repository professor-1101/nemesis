# ReportPortal Code Review Plan
## تحلیل کامل و کد ریویو سیستم ReportPortal Integration

---

## 📋 Overview
این سند شامل پلن کامل برای کد ریویو و تحلیل سیستم ReportPortal Integration در Nemesis Framework است.

---

## 🎯 Task 1: تحلیل Launch Lifecycle Management

### هدف: بررسی کامل منطق start_launch و finish_launch

#### 1.1: بررسی `rp_launch_coordinator.py` - منطق start_launch
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_launch_coordinator.py`
- بررسی متد `start_launch()` (خطوط 64-125)
- نحوه دریافت `launch_id` از `client.start_launch()`
- ذخیره `launch_id` در `self.launch_id`
- ذخیره `launch_id` در `EnvironmentCoordinator`
- بررسی retry logic با `@retry` decorator
- بررسی exception handling

**سوالات کلیدی:**
- آیا `launch_id` همیشه از return value دریافت می‌شود؟
- آیا fallback به `client.launch_id` درست کار می‌کند؟
- آیا ذخیره در EnvironmentCoordinator موفق است؟

#### 1.2: بررسی `rp_launch_coordinator.py` - منطق finish_launch
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_launch_coordinator.py`
- بررسی متد `finish_launch()` (خطوط 144-250)
- مدیریت `target_launch_id` vs `client.launch_id`
- منطق set کردن `client.launch_id` اگر متفاوت باشد
- بررسی `launch_uuid` property
- بررسی timing و delays
- بررسی عدم پاک کردن `launch_id` بعد از finish

**سوالات کلیدی:**
- آیا `client.launch_id` همیشه با `target_launch_id` match می‌کند؟
- آیا set کردن `launch_uuid` کار می‌کند؟
- چرا `launch_id` پاک نمی‌شود بعد از finish؟

#### 1.3: بررسی `reportportal.py` - lazy launch start
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/reportportal.py`
- بررسی متد `start_feature()` (خطوط 132-174)
- منطق lazy launch start
- auto-generation `launch_description` از feature
- auto-generation `launch_attributes` از tags
- فراخوانی `start_launch()` با description و attributes

**سوالات کلیدی:**
- آیا `_launch_started` flag درست set می‌شود؟
- آیا `launch_description` درست از feature description استخراج می‌شود؟
- آیا `launch_attributes` درست از tags parse می‌شوند؟

#### 1.4: بررسی `report_finalizer.py` - terminate() و direct API
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/report_finalizer.py`
- بررسی متد `finalize()` (خطوط 21-160)
- دریافت `launch_id` از `_finished_launch_id` یا `launch_id` property
- فراخوانی `finish_launch()` با explicit `launch_id`
- فراخوانی `terminate()` برای flush کردن async queue
- فراخوانی `_finish_launch_direct_api()` به عنوان fallback
- پاک کردن `launch_id` بعد از terminate

**سوالات کلیدی:**
- آیا `launch_id` درست از `_finished_launch_id` دریافت می‌شود؟
- آیا `terminate()` درست queue را flush می‌کند؟
- آیا direct API call درست کار می‌کند؟

#### 1.5: بررسی EnvironmentCoordinator - ذخیره و بازیابی launch_id
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/environment_coordinator.py`
- بررسی `rp_launch_id` attribute
- ذخیره `launch_id` در `before_all` یا `start_launch`
- بازیابی `launch_id` در `finish_launch` یا `finalize`
- پاک کردن `launch_id` بعد از terminate

**سوالات کلیدی:**
- آیا `rp_launch_id` درست set می‌شود؟
- آیا cross-process access کار می‌کند؟
- آیا cleanup درست انجام می‌شود؟

---

## 🎯 Task 2: تحلیل Feature Lifecycle Management

### هدف: بررسی کامل منطق start_feature و finish_feature

#### 2.1: بررسی `rp_feature_handler.py` - start_feature
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_feature_handler.py`
- بررسی متد `start_feature()` (خطوط 33-82)
- ایجاد SUITE item با `start_test_item()`
- parse کردن tags برای attributes
- دریافت `launch_id` از `rp_launch_manager`
- ذخیره `feature_id` در `self.feature_id`

**سوالات کلیدی:**
- آیا `launch_id` همیشه موجود است؟
- آیا SUITE item درست ایجاد می‌شود؟
- آیا attributes درست parse می‌شوند؟

#### 2.2: بررسی `rp_feature_handler.py` - finish_feature
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_feature_handler.py`
- بررسی متد `finish_feature()` (خطوط 86-109)
- فراخوانی `finish_test_item()` با `feature_id`
- بررسی `is_launch_active()` قبل از finish
- پاک کردن `feature_id` بعد از finish

**سوالات کلیدی:**
- آیا `feature_id` همیشه موجود است؟
- آیا `is_launch_active()` درست کار می‌کند؟
- آیا finish درست انجام می‌شود؟

#### 2.3: بررسی `feature_handler.py` - استخراج description و tags
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/feature_handler.py`
- بررسی متد `start_feature()` (خطوط 39-62)
- استخراج `feature_name` از feature object
- استخراج `description` از feature object (list یا string)
- استخراج `tags` از feature object
- تبدیل description به string
- فراخوانی `rp_client.start_feature()`

**سوالات کلیدی:**
- آیا `description` درست استخراج می‌شود؟
- آیا list description درست به string تبدیل می‌شود؟
- آیا tags درست استخراج می‌شوند؟

#### 2.4: بررسی `reporting_environment.py` - فراخوانی start_feature
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/reporting_environment.py`
- بررسی متد `start_feature()` (خطوط 126-136)
- فراخوانی `report_manager.start_feature()`
- بررسی `report_manager` availability

**سوالات کلیدی:**
- آیا `report_manager` همیشه موجود است؟
- آیا exception handling درست است؟

#### 2.5: بررسی `feature_hooks.py` - before_feature و after_feature
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/feature_hooks.py`
- بررسی `before_feature()` hook (خطوط 18-35)
- بررسی `after_feature()` hook (خطوط 37-55)
- فراخوانی `reporting_env.start_feature()` و `end_feature()`
- exception handling با `@handle_exceptions_with_fallback`

**سوالات کلیدی:**
- آیا hooks درست فراخوانی می‌شوند؟
- آیا exception handling درست است؟

---

## 🎯 Task 3: تحلیل Scenario/Test Lifecycle Management

### هدف: بررسی کامل منطق start_test و finish_test

#### 3.1: بررسی `rp_test_handler.py` - start_test
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_test_handler.py`
- بررسی متد `start_test()` (خطوط 40-115)
- ایجاد SCENARIO item با `start_test_item()`
- parse کردن tags برای attributes و test_case_id
- دریافت `feature_id` از `rp_feature_manager`
- دریافت `launch_id` از `rp_launch_manager`
- ذخیره `test_id` در `self.test_id`

**سوالات کلیدی:**
- آیا `feature_id` همیشه موجود است؟
- آیا SCENARIO item درست ایجاد می‌شود؟
- آیا scenario name درست است (بدون "Scenario:" prefix)؟

#### 3.2: بررسی `rp_test_handler.py` - finish_test
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_test_handler.py`
- بررسی متد `finish_test()` (خطوط 117-167)
- فراخوانی `finish_test_item()` با `test_id`
- بررسی `is_launch_active()` قبل از finish
- تبدیل status به ReportPortal format
- handling skipped tests با `is_skipped_an_issue`

**سوالات کلیدی:**
- آیا `test_id` همیشه موجود است؟
- آیا `is_launch_active()` درست کار می‌کند؟
- آیا status درست convert می‌شود؟

#### 3.3: بررسی `scenario_handler.py` - استخراج scenario name و status
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/scenario_handler.py`
- بررسی متد `start_scenario()` (خطوط 35-54)
- بررسی متد `end_scenario()` (خطوط 55-90)
- استخراج `scenario_name` از scenario object
- استخراج `status` از scenario object
- normalize کردن status با `normalize_scenario_status_for_rp()`
- فراخوانی `rp_client.start_test()` و `finish_test()`

**سوالات کلیدی:**
- آیا scenario name درست استخراج می‌شود؟
- آیا status درست normalize می‌شود؟

#### 3.4: بررسی `scenario_hooks.py` - before_scenario و after_scenario
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/scenario_hooks.py`
- بررسی `before_scenario()` hook (خطوط 12-74)
- بررسی `after_scenario()` hook (خطوط 83-116)
- فراخوانی `reporting_env.start_scenario()` و `end_scenario()`
- exception handling

**سوالات کلیدی:**
- آیا hooks درست فراخوانی می‌شوند؟

#### 3.5: بررسی `is_launch_active()` - چک کردن launch_id
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_launch_coordinator.py`
- بررسی متد `is_launch_active()` (خطوط 133-135)
- بررسی `self.launch_id is not None`
- استفاده در `finish_test()` و `finish_feature()`

**سوالات کلیدی:**
- آیا `is_launch_active()` درست کار می‌کند؟
- آیا `launch_id` همیشه درست set است؟

---

## 🎯 Task 4: تحلیل Step Lifecycle Management

### هدف: بررسی کامل منطق start_step و finish_step

#### 4.1: بررسی `rp_step_handler.py` - start_step
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_step_handler.py`
- بررسی متد `start_step()` (خطوط 40-90)
- ایجاد STEP item با `start_test_item()`
- دریافت `test_id` از `rp_test_manager`
- دریافت `launch_id` از `rp_launch_manager`
- ذخیره `step_id` در `self.step_id`

**سوالات کلیدی:**
- آیا `test_id` همیشه موجود است؟
- آیا STEP item درست ایجاد می‌شود؟

#### 4.2: بررسی `rp_step_handler.py` - finish_step
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_step_handler.py`
- بررسی متد `finish_step()` (خطوط 92-164)
- فراخوانی `finish_test_item()` با `step_id`
- تبدیل status به ReportPortal format
- handling step logs

**سوالات کلیدی:**
- آیا `step_id` همیشه موجود است؟
- آیا status درست convert می‌شود؟

#### 4.3: بررسی `step_hooks.py` - before_step و after_step
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/step_hooks.py`
- بررسی `before_step()` hook (خطوط 19-54)
- بررسی `after_step()` hook (خطوط 56-90)
- فراخوانی `reporting_env.start_step()` و `end_step()`

**سوالات کلیدی:**
- آیا hooks درست فراخوانی می‌شوند؟

#### 4.4: بررسی step_log_layout - SCENARIO, STEP, NESTED modes
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_step_handler.py`
- بررسی `step_log_layout` configuration
- بررسی SCENARIO mode (logs only)
- بررسی STEP mode (flat items)
- بررسی NESTED mode (hierarchical)

**سوالات کلیدی:**
- آیا layout درست اعمال می‌شود؟

#### 4.5: بررسی hierarchy management - parent-child relationships
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_step_handler.py`
- بررسی parent-child relationships
- Launch -> Feature (SUITE) -> Scenario (TEST) -> Step (STEP)
- بررسی `parent_item_id` در `start_test_item()`

**سوالات کلیدی:**
- آیا hierarchy درست است؟

---

## 🎯 Task 5: تحلیل Configuration Management

### هدف: بررسی کامل configuration loading و auto-generation

#### 5.1: بررسی `rp_config_loader.py` - load و validate
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_config_loader.py`
- بررسی `_load_config()` (خطوط 32-68)
- خواندن endpoint, project, api_key
- خواندن launch_name, launch_description, launch_attributes
- بررسی `_validate_config()` (خطوط 91-107)

**سوالات کلیدی:**
- آیا configuration درست load می‌شود؟
- آیا validation درست است؟

#### 5.2: بررسی auto-generation - launch_name از execution_id
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_config_loader.py`
- بررسی خطوط 38-46
- دریافت `execution_id` از `ExecutionContext`
- ساخت `launch_name` از execution_id

**سوالات کلیدی:**
- آیا execution_id درست دریافت می‌شود؟
- آیا launch_name درست generate می‌شود؟

#### 5.3: بررسی auto-generation - launch_description از feature
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/reportportal.py`
- بررسی خطوط 145-156
- استخراج description از feature
- تبدیل list به string
- استفاده از feature name اگر description نباشد

**سوالات کلیدی:**
- آیا description درست استخراج می‌شود؟
- آیا list به string درست تبدیل می‌شود؟

#### 5.4: بررسی auto-generation - launch_attributes از tags
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/reportportal.py`
- بررسی خطوط 158-164
- parse کردن tags با `RPUtils.parse_behave_tags()`
- استخراج attributes از parsed tags

**سوالات کلیدی:**
- آیا tags درست parse می‌شوند؟
- آیا attributes درست استخراج می‌شوند؟

#### 5.5: بررسی reportportal.yaml - خواندن تنظیمات
**فایل:** `nemesis/saucedemo-automation/conf/reportportal.yaml`
- بررسی ساختار فایل
- بررسی endpoint, project, api_key
- بررسی launch settings (commented out)
- بررسی client_type, verify_ssl

**سوالات کلیدی:**
- آیا فایل درست خوانده می‌شود؟
- آیا commented settings درست handle می‌شوند؟

---

## 🎯 Task 6: تحلیل Error Handling و Exception Management

### هدف: بررسی کامل exception handling و error recovery

#### 6.1: بررسی @safe_execute decorator
**فایل:** `nemesis/Nemesis/src/nemesis/utils/decorators/safe_execute.py`
- بررسی decorator implementation
- exception catching و logging
- return value handling

**سوالات کلیدی:**
- آیا exceptions درست catch می‌شوند؟
- آیا logging درست است؟

#### 6.2: بررسی @retry decorator
**فایل:** `nemesis/Nemesis/src/nemesis/utils/decorators/retry.py`
- بررسی retry logic
- max_attempts و delay
- exception handling در retries

**سوالات کلیدی:**
- آیا retry logic درست کار می‌کند؟

#### 6.3: بررسی handle_exceptions_with_fallback
**فایل:** `nemesis/Nemesis/src/nemesis/utils/decorators/exception_handler.py`
- بررسی decorator implementation (خطوط 150-272)
- specific_exceptions vs fallback
- logging levels

**سوالات کلیدی:**
- آیا fallback mechanism درست کار می‌کند؟

#### 6.4: بررسی ReportPortalError
**فایل:** `nemesis/Nemesis/src/nemesis/shared/exceptions.py`
- بررسی custom exception class
- error message formatting

**سوالات کلیدی:**
- آیا exception درست raise می‌شود؟

#### 6.5: بررسی error logging
**فایل:** همه فایل‌های reporting
- بررسی error logging در handlers
- بررسی traceback logging
- بررسی error recovery

**سوالات کلیدی:**
- آیا errors درست log می‌شوند؟
- آیا recovery درست است؟

---

## 🎯 Task 7: تحلیل Client Initialization و Connection Management

### هدف: بررسی کامل initialization flow و connection handling

#### 7.1: بررسی ReportPortalClient.__init__
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/reportportal.py`
- بررسی خطوط 19-111
- بررسی ReportPortal enabled check
- ایجاد RPClientBase
- ایجاد handlers (launch, feature, test, step)
- بررسی existing launch_id

**سوالات کلیدی:**
- آیا initialization درست است؟
- آیا existing launch_id درست handle می‌شود؟

#### 7.2: بررسی RPClientBase - connection validation
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/report_portal/rp_client_base.py`
- بررسی `_validate_connection()`
- بررسی endpoint, project, api_key validation

**سوالات کلیدی:**
- آیا connection validation درست است؟

#### 7.3: بررسی reporter_coordinator.py - _init_rp_client
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/reporter_coordinator.py`
- بررسی `_init_rp_client()` (خطوط 91-109)
- exception handling
- logging

**سوالات کلیدی:**
- آیا initialization درست است؟

#### 7.4: بررسی lazy initialization
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/reportportal.py`
- بررسی lazy launch start
- بررسی `_launch_started` flag
- بررسی launch start در first feature

**سوالات کلیدی:**
- آیا lazy initialization درست کار می‌کند؟

#### 7.5: بررسی connection reuse
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/reportportal.py`
- بررسی reuse existing launch_id
- بررسی launch_id از EnvironmentCoordinator

**سوالات کلیدی:**
- آیا connection reuse درست است؟

---

## 🎯 Task 8: تحلیل Async Queue Management و Termination

### هدف: بررسی کامل async queue handling و termination

#### 8.1: بررسی reportportal-client async queue
**فایل:** بررسی reportportal-client library
- بررسی نحوه کار async queue
- بررسی queue flushing
- بررسی request batching

**سوالات کلیدی:**
- آیا queue درست کار می‌کند؟

#### 8.2: بررسی terminate() - flush کردن queue
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/report_finalizer.py`
- بررسی خطوط 117-125
- فراخوانی `client.terminate()`
- بررسی queue flushing

**سوالات کلیدی:**
- آیا terminate() درست queue را flush می‌کند؟

#### 8.3: بررسی report_finalizer.py - terminate() و direct API
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/report_finalizer.py`
- بررسی خطوط 114-160
- فراخوانی terminate()
- فراخوانی direct API call
- timing و delays

**سوالات کلیدی:**
- آیا sequence درست است؟

#### 8.4: بررسی _finish_launch_direct_api - fallback
**فایل:** `nemesis/Nemesis/src/nemesis/reporting/management/report_finalizer.py`
- بررسی متد `_finish_launch_direct_api()` (خطوط 162-220)
- ساخت direct API request
- فراخوانی ReportPortal API
- error handling

**سوالات کلیدی:**
- آیا direct API call درست کار می‌کند؟

#### 8.5: بررسی timing issues - sleep delays
**فایل:** همه فایل‌های reporting
- بررسی sleep delays
- بررسی timing بین finish و terminate
- بررسی queue flushing timing

**سوالات کلیدی:**
- آیا timing درست است؟

---

## 🎯 Task 9: تحلیل Data Flow و State Management

### هدف: بررسی کامل flow داده‌ها و state management

#### 9.1: بررسی launch_id flow
**فایل:** همه فایل‌های reporting
- از `start_launch()` تا `finish_launch()`
- ذخیره در `self.launch_id`
- ذخیره در `EnvironmentCoordinator`
- ذخیره در `_finished_launch_id`
- بازیابی در `finalize()`

**سوالات کلیدی:**
- آیا launch_id درست flow می‌کند؟

#### 9.2: بررسی feature_id flow
**فایل:** `rp_feature_handler.py`
- از `start_feature()` تا `finish_feature()`
- ذخیره در `self.feature_id`
- استفاده در `start_test()` به عنوان parent

**سوالات کلیدی:**
- آیا feature_id درست flow می‌کند؟

#### 9.3: بررسی test_id flow
**فایل:** `rp_test_handler.py`
- از `start_test()` تا `finish_test()`
- ذخیره در `self.test_id`
- استفاده در `start_step()` به عنوان parent

**سوالات کلیدی:**
- آیا test_id درست flow می‌کند؟

#### 9.4: بررسی step_id flow
**فایل:** `rp_step_handler.py`
- از `start_step()` تا `finish_step()`
- ذخیره در `self.step_id`

**سوالات کلیدی:**
- آیا step_id درست flow می‌کند؟

#### 9.5: بررسی state cleanup
**فایل:** همه فایل‌های reporting
- پاک کردن IDs بعد از finish
- پاک کردن از EnvironmentCoordinator
- timing cleanup

**سوالات کلیدی:**
- آیا cleanup درست است؟

---

## 🎯 Task 10: تحلیل Integration Points و Hook Execution

### هدف: بررسی کامل integration points و hook execution order

#### 10.1: بررسی hooks.py - before_all و after_all
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/hooks.py`
- بررسی `before_all()` hook
- بررسی `after_all()` hook
- فراخوانی EnvironmentCoordinator methods

**سوالات کلیدی:**
- آیا hooks درست فراخوانی می‌شوند؟

#### 10.2: بررسی feature_hooks.py
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/feature_hooks.py`
- بررسی `before_feature()` و `after_feature()`
- execution order

**سوالات کلیدی:**
- آیا execution order درست است؟

#### 10.3: بررسی scenario_hooks.py
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/scenario_hooks.py`
- بررسی `before_scenario()` و `after_scenario()`
- execution order

**سوالات کلیدی:**
- آیا execution order درست است؟

#### 10.4: بررسی step_hooks.py
**فایل:** `nemesis/Nemesis/src/nemesis/infrastructure/environment/step_hooks.py`
- بررسی `before_step()` و `after_step()`
- execution order

**سوالات کلیدی:**
- آیا execution order درست است؟

#### 10.5: بررسی execution order - ترتیب فراخوانی
**فایل:** همه فایل‌های hooks
- ترتیب کلی: before_all -> before_feature -> before_scenario -> before_step -> after_step -> after_scenario -> after_feature -> after_all
- ترتیب reporting calls
- ترتیب cleanup

**سوالات کلیدی:**
- آیا execution order درست است؟

---

## 📊 Lifecycle Reporting Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    REPORTING LIFECYCLE                      │
└─────────────────────────────────────────────────────────────┘

1. INITIALIZATION PHASE
   ├─ ReportPortalClient.__init__()
   ├─ RPClientBase creation
   ├─ Handlers initialization (launch, feature, test, step)
   └─ Configuration loading

2. BEFORE_ALL HOOK
   ├─ EnvironmentCoordinator setup
   └─ Browser environment initialization

3. BEFORE_FEATURE HOOK
   ├─ reporting_env.start_feature()
   │  ├─ feature_handler.start_feature()
   │  │  ├─ Extract feature name, description, tags
   │  │  └─ rp_client.start_feature()
   │  │     ├─ Lazy launch start (if not started)
   │  │     │  ├─ Auto-generate launch_description
   │  │     │  ├─ Auto-generate launch_attributes
   │  │     │  └─ rp_launch_manager.start_launch()
   │  │     │     ├─ client.start_launch()
   │  │     │     ├─ Store launch_id
   │  │     │     └─ Store in EnvironmentCoordinator
   │  │     └─ rp_feature_manager.start_feature()
   │  │        ├─ Get launch_id
   │  │        └─ client.start_test_item() [SUITE]
   └─ Store feature_id

4. BEFORE_SCENARIO HOOK
   ├─ reporting_env.start_scenario()
   │  ├─ scenario_handler.start_scenario()
   │  │  └─ rp_client.start_test()
   │  │     └─ rp_test_manager.start_test()
   │  │        ├─ Get feature_id
   │  │        ├─ Get launch_id
   │  │        └─ client.start_test_item() [SCENARIO]
   └─ Store test_id

5. BEFORE_STEP HOOK
   ├─ reporting_env.start_step()
   │  └─ rp_client.start_step()
   │     └─ rp_step_manager.start_step()
   │        ├─ Get test_id
   │        ├─ Get launch_id
   │        └─ client.start_test_item() [STEP]
   └─ Store step_id

6. STEP EXECUTION
   └─ (Test execution happens here)

7. AFTER_STEP HOOK
   ├─ reporting_env.end_step()
   │  └─ rp_client.finish_step()
   │     └─ rp_step_manager.finish_step()
   │        └─ client.finish_test_item() [STEP]
   └─ (Keep step_id for attachments)

8. AFTER_SCENARIO HOOK
   ├─ reporting_env.end_scenario()
   │  ├─ scenario_handler.end_scenario()
   │  │  └─ rp_client.finish_test()
   │  │     └─ rp_test_manager.finish_test()
   │  │        ├─ Check is_launch_active()
   │  │        └─ client.finish_test_item() [SCENARIO]
   └─ (Keep test_id for attachments)

9. AFTER_FEATURE HOOK
   ├─ reporting_env.end_feature()
   │  └─ rp_client.finish_feature()
   │     └─ rp_feature_manager.finish_feature()
   │        ├─ Check is_launch_active()
   │        └─ client.finish_test_item() [SUITE]
   └─ Clear feature_id

10. AFTER_ALL HOOK
    ├─ EnvironmentCoordinator cleanup
    └─ Browser environment cleanup

11. FINALIZATION PHASE
    ├─ ReportFinalizer.finalize()
    │  ├─ Get launch_id from _finished_launch_id or launch_id property
    │  ├─ rp_client.finish_launch()
    │  │  └─ rp_launch_manager.finish_launch()
    │  │     ├─ Check client.launch_id vs target_launch_id
    │  │     ├─ Set launch_uuid if needed
    │  │     └─ client.finish_launch()
    │  ├─ Sleep for queue processing
    │  ├─ client.terminate() [Flush async queue]
    │  ├─ _finish_launch_direct_api() [Fallback]
    │  └─ Clear launch_id from EnvironmentCoordinator
    └─ Cleanup complete
```

---

## 🔍 Key Issues to Investigate

1. **Launch Description Issue**
   - Why is it showing "Test execution for: Test Feature"?
   - Is description correctly extracted from feature?
   - Is description correctly passed to start_launch?

2. **Launch Not Closing**
   - Is finish_launch() called?
   - Is terminate() called?
   - Is direct API call working?
   - Is launch_id correctly maintained?

3. **Test Items Not Showing**
   - Are scenarios created?
   - Are finish_test() calls working?
   - Is is_launch_active() returning True?

4. **Logger Not Showing RP DEBUG Logs**
   - Is logger configured correctly?
   - Are log levels correct?
   - Are logs being filtered?

---

## 📝 Review Checklist

- [ ] All lifecycle methods reviewed
- [ ] All exception handlers reviewed
- [ ] All state management reviewed
- [ ] All integration points reviewed
- [ ] All configuration loading reviewed
- [ ] All error handling reviewed
- [ ] All logging reviewed
- [ ] All cleanup reviewed

---

## 🎯 Next Steps

1. Start with Task 1 - Launch Lifecycle
2. Review each subtask systematically
3. Document findings
4. Identify root causes
5. Propose fixes
6. Implement fixes
7. Test fixes
8. Verify in ReportPortal

---

**Created:** 2025-12-19
**Status:** In Progress
**Priority:** High


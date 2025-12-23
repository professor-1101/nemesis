# 🎯 Nemesis Framework & PostBank - پلن جامع Refactoring

## 📋 خلاصه مشکلات یافت شده

### 🔴 **اولویت بالا (Critical)**

1. **Performance Metrics به صورت Attribute ارسال نمی‌شوند**
   - 📍 Location: `Nemesis/src/nemesis/reporting/management/scenario_handler.py:118-126`
   - ❌ Problem: Metrics به صورت INFO message لاگ می‌شوند نه ReportPortal Attributes
   - 💥 Impact: Metrics در UI ReportPortal قابل مشاهده نیستند، فیلتر و جستجو غیرممکن است

2. **Action Logs جزئیات کافی ندارند**
   - 📍 Location: `Nemesis/src/nemesis/infrastructure/browser/playwright_adapter.py:76-83`
   - ❌ Problem: فقط selector لاگ می‌شود، tag name المان ثبت نمی‌شود
   - 💥 Impact: برای دیباگ نمی‌توان فهمید روی کدام نوع المان کلیک شد (button, input, div, etc.)

3. **Scenario Dependencies - سناریوها به هم وابسته‌اند**
   - 📍 Location: `PostBank/features/sabte_motaghazi_*/`
   - ❌ Problem: Feature دوم به login وابسته است
   - 💥 Impact: نمی‌توان سناریوها را مستقل اجرا کرد، تست‌ها fragile هستند

4. **Shared Browser State بین سناریوها**
   - 📍 Location: `Nemesis/src/nemesis/infrastructure/environment/step_hooks.py:82`
   - ❌ Problem: Browser session بین سناریوها reset نمی‌شود
   - 💥 Impact: cookies/localStorage از scenario قبلی باقی می‌ماند، تست‌ها ممکن است تداخل داشته باشند

5. **Network Logs فرمت استاندارد HAR ندارد**
   - 📍 Location: `Nemesis/src/nemesis/infrastructure/collectors/network.py:201-235`
   - ❌ Problem: JSON سفارشی است نه HAR format
   - 💥 Impact: نمی‌توان با ابزارهای استاندارد (Chrome DevTools, HAR Viewer) analyze کرد

### 🟡 **اولویت متوسط (Important)**

6. **Console Logs - Readability پایین**
   - 📍 Location: `Nemesis/src/nemesis/reporting/management/step_handler.py:382-451`
   - ❌ Problem:
     - محدودیت 50 log
     - Truncate شدن messages بیش از 5000 کاراکتر
     - فرمت خوانا نیست در ReportPortal
   - 💥 Impact: لاگ‌های مهم ممکن است از دست بروند

7. **Network Logs - اطلاعات محدود در ReportPortal**
   - 📍 Location: `Nemesis/src/nemesis/reporting/management/step_handler.py:313-362`
   - ❌ Problem:
     - فقط 10 request اول نشان داده می‌شود
     - URL truncate به 100 کاراکتر
     - POST data truncate به 1000 کاراکتر
   - 💥 Impact: اطلاعات کامل network activity قابل مشاهده نیست

8. **Step-level Reporting - بسته به Config متفاوت است**
   - 📍 Location: `Nemesis/src/nemesis/reporting/report_portal/rp_step_handler.py:84-132`
   - ❌ Problem: سه حالت SCENARIO/STEP/NESTED با رفتار متفاوت
   - 💥 Impact: کاربر باید config را درست تنظیم کند تا logs زیر step درست نشان داده شوند

9. **Stack Trace Truncation**
   - 📍 Location: `Nemesis/src/nemesis/reporting/report_portal/rp_logger.py:97`
   - ❌ Problem: Stack traces بیش از 15000 کاراکتر truncate می‌شوند
   - 💥 Impact: ممکن است قسمت مهم stack trace از دست برود

### 🟢 **اولویت پایین (Nice to Have)**

10. **PostBank Page Objects - SRP Violation**
    - 📍 Location: `PostBank/pages/applicant_registration_page.py:363`
    - ❌ Problem: Page Object هم با UI کار می‌کند هم داده تصادفی تولید می‌کند (متد 300 خطی)
    - 💥 Impact: Maintainability پایین، testing سخت‌تر

11. **PostBank Step Definitions - Complexity بالا**
    - 📍 Location: `PostBank/features/steps/login_steps.py:516`
    - ❌ Problem: منطق پیچیده data loading با سه سطح priority
    - 💥 Impact: Code خوانایی پایین دارد

12. **Debug Print Statements در Production**
    - 📍 Location: `PostBank/features/steps/*.py`
    - ❌ Problem: `print()` به جای logging استفاده شده
    - 💥 Impact: لاگ‌ها به صورت حرفه‌ای مدیریت نمی‌شوند

---

## 🗺️ پلن Refactoring - 6 فاز

### **Phase 1: ReportPortal Action Logging Enhancement** 🎯
**زمان تخمینی:** 4-6 ساعت
**اولویت:** Critical

#### هدف:
Action logs باید جزئیات کامل داشته باشند شامل:
- Element selector
- Element tag name (button, input, div, etc.)
- Element role/aria-label (اگر وجود دارد)
- Action type (click, fill, navigate, etc.)
- Value (برای fill)

#### تغییرات لازم:

**1.1. توسعه PlaywrightPageAdapter**

```python
# File: Nemesis/src/nemesis/infrastructure/browser/playwright_adapter.py

def _get_element_details(self, selector: str) -> dict[str, Any]:
    """Extract detailed element information for logging."""
    try:
        element = self._page.locator(selector).first

        # Get tag name
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")

        # Get role
        role = element.get_attribute("role") or ""

        # Get aria-label
        aria_label = element.get_attribute("aria-label") or ""

        # Get text content (limited)
        text = element.inner_text()[:50] if element.is_visible() else ""

        # Get element type (for input)
        elem_type = element.get_attribute("type") if tag_name == "input" else ""

        return {
            "tag": tag_name,
            "role": role,
            "aria_label": aria_label,
            "text": text,
            "type": elem_type,
        }
    except Exception as e:
        self._logger.debug(f"Could not extract element details: {e}")
        return {}

def _log_action(self, action: str, selector: str = "", details: str = "") -> None:
    """Log action with enhanced element details."""
    # Build detailed message
    parts = [f"[ACTION] {action}"]

    if selector:
        parts.append(f"Selector: {selector}")

        # Get element details
        elem_details = self._get_element_details(selector)
        if elem_details:
            tag_info = f"<{elem_details.get('tag', 'unknown')}>"
            if elem_details.get('type'):
                tag_info += f"[type={elem_details['type']}]"
            parts.append(f"Element: {tag_info}")

            if elem_details.get('aria_label'):
                parts.append(f"ARIA Label: {elem_details['aria_label']}")
            elif elem_details.get('text'):
                parts.append(f"Text: {elem_details['text']}")

    if details:
        parts.append(f"Details: {details}")

    message = " | ".join(parts)

    # Log to local logger
    self._logger.info(message)

    # Log to ReportPortal
    if self._action_logger:
        self._action_logger(message)
```

**1.2. بروزرسانی همه action methods:**

```python
def click(self, selector: str, **options) -> None:
    """Click element with enhanced logging."""
    self._log_action("CLICK", selector=selector)
    self._page.click(selector, **options)

def fill(self, selector: str, value: str, **options) -> None:
    """Fill input with enhanced logging."""
    # Mask sensitive data
    display_value = "***" if "password" in selector.lower() else value[:50]
    self._log_action("FILL", selector=selector, details=f"Value: {display_value}")
    self._page.fill(selector, value, **options)
```

**1.3. Configuration برای masking sensitive data:**

```yaml
# File: conf/logging.yaml
action_logging:
  enabled: true
  include_element_details: true
  sensitive_selectors:
    - password
    - secret
    - token
    - api_key
  mask_character: "***"
```

#### تست:
- تست با عناصر مختلف (button, input, div, a)
- تست با ARIA labels
- تست masking برای password fields
- بررسی لاگ‌ها در ReportPortal

---

### **Phase 2: Performance Metrics as ReportPortal Attributes** 📊
**زمان تخمینی:** 6-8 ساعت
**اولویت:** Critical

#### هدف:
Performance metrics باید:
1. به صورت **Attributes** به scenario/test ارسال شوند
2. در ReportPortal UI قابل فیلتر و جستجو باشند
3. به صورت summary و detailed هر دو موجود باشند

#### مشکل فعلی:
```python
# scenario_handler.py:118-126
# فقط به صورت INFO message لاگ می‌شود
rp_client.log_message(f"Performance Metrics:\n\n{perf_summary}", "INFO")
```

#### راه حل:

**2.1. اضافه کردن attributes هنگام start_test:**

```python
# File: Nemesis/src/nemesis/reporting/report_portal/rp_test_handler.py

def start_test(self, test_name: str, tags: list = None, metrics: dict = None) -> None:
    """Start test with optional performance metrics as attributes."""

    attributes = []

    # Add tags
    if tags:
        attributes.extend([{"key": "tag", "value": tag} for tag in tags])

    # Add metrics as attributes (if provided)
    if metrics:
        attributes.extend(self._format_metrics_as_attributes(metrics))

    start_params = {
        "name": test_name,
        "start_time": RPUtils.timestamp(),
        "item_type": "STEP",
        "parent_item_id": feature_id,
        "launch_uuid": launch_id,
        "attributes": attributes,  # ✅ اضافه شد
        "has_stats": True,
    }

    self.test_id = self.client.start_test_item(**start_params)

def _format_metrics_as_attributes(self, metrics: dict) -> list[dict]:
    """Format performance metrics as RP attributes."""
    attributes = []

    # Navigation metrics
    if 'navigation' in metrics:
        nav = metrics['navigation']
        attributes.append({"key": "perf.load_time", "value": f"{nav.get('total_load', 0):.0f}ms"})
        attributes.append({"key": "perf.ttfb", "value": f"{nav.get('ttfb', 0):.0f}ms"})
        attributes.append({"key": "perf.dns", "value": f"{nav.get('dns_lookup', 0):.0f}ms"})

    # Web Vitals
    if 'web_vitals' in metrics:
        vitals = metrics['web_vitals']
        attributes.append({"key": "perf.fcp", "value": f"{vitals.get('fcp', 0):.0f}ms"})
        attributes.append({"key": "perf.lcp", "value": f"{vitals.get('lcp', 0):.0f}ms"})
        attributes.append({"key": "perf.cls", "value": f"{vitals.get('cls', 0):.3f}"})

    # Memory
    if 'memory' in metrics:
        mem = metrics['memory']
        attributes.append({"key": "perf.memory_mb", "value": f"{mem.get('used_js_heap', 0)/1024/1024:.1f}"})

    # Resources
    if 'resources' in metrics:
        res = metrics['resources']
        attributes.append({"key": "perf.resource_count", "value": str(res.get('total_count', 0))})
        attributes.append({"key": "perf.transfer_kb", "value": f"{res.get('total_transfer', 0)/1024:.1f}"})

    return attributes
```

**⚠️ مشکل: Attributes can't be added AFTER test starts**

راه حل جایگزین - **Update Test Item:**

```python
# File: Nemesis/src/nemesis/reporting/report_portal/rp_test_handler.py

def update_test_attributes(self, attributes: list[dict]) -> None:
    """Update test attributes after collection."""
    if not self.test_id:
        self._logger.warning("No active test ID to update attributes")
        return

    try:
        # ReportPortal API: Update test item
        self.client.update_test_item(
            item_uuid=self.test_id,
            attributes=attributes
        )
        self._logger.info(f"Updated test attributes: {len(attributes)} metrics added")
    except Exception as e:
        self._logger.error(f"Failed to update test attributes: {e}")
```

**2.2. Collect metrics BEFORE finishing test:**

```python
# File: Nemesis/src/nemesis/reporting/management/scenario_handler.py

def finish_scenario(self, scenario, status: str = "passed") -> None:
    """Finish scenario with metrics as attributes."""

    # Collect performance metrics
    perf_collector = self._get_collector('performance')
    if perf_collector:
        metrics = perf_collector.collect_all()

        # Update test attributes with metrics
        def _update_metrics():
            rp_client = self.reporter_manager.get_rp_client()
            attributes = rp_client._format_metrics_as_attributes(metrics)
            rp_client.update_test_attributes(attributes)

        self._call_rp_client(_update_metrics)

    # Finish test
    def _finish():
        self.reporter_manager.get_rp_client().finish_test(status)

    self._call_rp_client(_finish)
```

**2.3. Configuration:**

```yaml
# File: conf/reporting.yaml
performance_metrics:
  enabled: true
  as_attributes: true  # ✅ ارسال به صورت attributes
  as_logs: true        # ✅ همچنین به صورت log message
  metrics_to_include:
    - load_time
    - ttfb
    - fcp
    - lcp
    - cls
    - memory
    - resource_count
```

#### تست:
- بررسی attributes در ReportPortal UI
- فیلتر کردن scenarios بر اساس metrics (مثلاً load_time > 2000ms)
- تست با performance budget (fail اگر metric از threshold بالاتر رفت)

---

### **Phase 3: Console & Network Logs Readability Enhancement** 📝
**زمان تخمینی:** 5-7 ساعت
**اولویت:** Critical

#### هدف:
1. Console logs خوانا و کامل در ReportPortal
2. Network logs در فرمت استاندارد HAR
3. بدون truncation (یا با pagination)
4. Formatting حرفه‌ای

#### 3.1. Console Logs Enhancement:

**مشکل فعلی:**
```python
# step_handler.py:434
console_text = "\n".join(str(log) for log in console_collector[:50])  # ❌ فقط 50 log
```

**راه حل:**

```python
# File: Nemesis/src/nemesis/reporting/management/step_handler.py

def _attach_console_logs_enhanced(self, rp_client, step_name: str) -> None:
    """Attach console logs with better formatting and no truncation."""
    console_collector = self._get_collector_data('console')
    if not console_collector:
        return

    # Separate by severity
    errors = [log for log in console_collector if log.get('type') == 'error']
    warnings = [log for log in console_collector if log.get('type') == 'warning']
    logs = [log for log in console_collector if log.get('type') in ('log', 'info')]

    # Format for better readability
    sections = []

    if errors:
        sections.append(self._format_console_section("ERRORS", errors, "🔴"))

    if warnings:
        sections.append(self._format_console_section("WARNINGS", warnings, "🟡"))

    if logs:
        sections.append(self._format_console_section("LOGS", logs, "🔵"))

    # Combine all sections
    full_console = "\n\n".join(sections)

    # Attach as file (no limit)
    rp_client.attach_file(
        full_console.encode('utf-8'),
        f"Console Logs: {step_name}",
        "text/plain"
    )

    # Also log summary
    summary = f"""
Console Summary:
  🔴 Errors: {len(errors)}
  🟡 Warnings: {len(warnings)}
  🔵 Logs: {len(logs)}
  📊 Total: {len(console_collector)}
"""
    rp_client.log_message(summary, "INFO")

def _format_console_section(self, title: str, logs: list, icon: str) -> str:
    """Format console logs section with nice formatting."""
    lines = [
        "=" * 80,
        f"{icon} {title} ({len(logs)} entries)",
        "=" * 80,
        ""
    ]

    for i, log in enumerate(logs, 1):
        lines.append(f"[{i}] {log.get('text', '')}")

        if log.get('location'):
            lines.append(f"    📍 Location: {log['location']}")

        if log.get('timestamp'):
            lines.append(f"    ⏱️  Time: {log['timestamp']:.0f}ms")

        lines.append("")  # Empty line between entries

    return "\n".join(lines)
```

**3.2. Network Logs HAR Format:**

```python
# File: Nemesis/src/nemesis/infrastructure/collectors/network.py

def export_as_har(self) -> dict:
    """Export network data in standard HAR format."""

    # HAR 1.2 format
    har = {
        "log": {
            "version": "1.2",
            "creator": {
                "name": "Nemesis Framework",
                "version": "1.0.0"
            },
            "pages": [{
                "startedDateTime": self._get_iso_timestamp(self.start_time),
                "id": "page_1",
                "title": "Test Execution",
                "pageTimings": {
                    "onContentLoad": -1,
                    "onLoad": -1
                }
            }],
            "entries": []
        }
    }

    # Convert requests to HAR entries
    request_map = {}
    for req in self.requests:
        if req['type'] == 'request':
            entry = {
                "startedDateTime": self._get_iso_timestamp(req['timestamp']),
                "time": 0,
                "request": {
                    "method": req['method'],
                    "url": req['url'],
                    "httpVersion": "HTTP/1.1",
                    "headers": [{"name": k, "value": v} for k, v in req.get('headers', {}).items()],
                    "queryString": [],
                    "cookies": [],
                    "headersSize": -1,
                    "bodySize": len(req.get('post_data', '')) if req.get('post_data') else 0,
                    "postData": {
                        "mimeType": "application/x-www-form-urlencoded",
                        "text": req.get('post_data', '')
                    } if req.get('post_data') else None
                },
                "response": {
                    "status": 0,
                    "statusText": "",
                    "httpVersion": "HTTP/1.1",
                    "headers": [],
                    "cookies": [],
                    "content": {
                        "size": 0,
                        "mimeType": "text/html"
                    },
                    "redirectURL": "",
                    "headersSize": -1,
                    "bodySize": -1
                },
                "cache": {},
                "timings": {
                    "blocked": -1,
                    "dns": -1,
                    "connect": -1,
                    "send": 0,
                    "wait": 0,
                    "receive": 0,
                    "ssl": -1
                },
                "pageref": "page_1"
            }
            request_map[req['url']] = entry
            har['log']['entries'].append(entry)

    # Update with responses
    for req in self.requests:
        if req['type'] == 'response' and req['url'] in request_map:
            entry = request_map[req['url']]
            entry['time'] = req.get('duration', 0)
            entry['response'] = {
                "status": req.get('status', 0),
                "statusText": req.get('status_text', ''),
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in req.get('headers', {}).items()],
                "cookies": [],
                "content": {
                    "size": req.get('size', 0),
                    "mimeType": req.get('content_type', 'text/html')
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": req.get('size', 0)
            }
            entry['timings']['wait'] = req.get('duration', 0)

    return har

def save_to_file(self, execution_id: str, scenario_name: str) -> Path:
    """Save as HAR file."""
    file_path = path_manager.get_attachment_path(execution_id, "network", "network.har")

    har_data = self.export_as_har()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(har_data, f, indent=2, ensure_ascii=False)

    return file_path
```

**3.3. Network Logs in ReportPortal - با جدول:**

```python
# File: Nemesis/src/nemesis/reporting/management/step_handler.py

def _log_network_activity_table(self, rp_client, step_name: str) -> None:
    """Log network activity as formatted table."""
    network_collector = self._get_collector_data('network')
    if not network_collector:
        return

    responses = [r for r in network_collector if r.get('type') == 'response']

    # Separate by status code
    success = [r for r in responses if 200 <= r.get('status', 0) < 300]
    redirects = [r for r in responses if 300 <= r.get('status', 0) < 400]
    client_errors = [r for r in responses if 400 <= r.get('status', 0) < 500]
    server_errors = [r for r in responses if r.get('status', 0) >= 500]

    # Create table
    table = self._create_network_table(responses)

    # Summary
    summary = f"""
Network Activity Summary:
  ✅ Success (2xx): {len(success)}
  ➡️  Redirects (3xx): {len(redirects)}
  ⚠️  Client Errors (4xx): {len(client_errors)}
  ❌ Server Errors (5xx): {len(server_errors)}
  📊 Total Requests: {len(responses)}

{table}
"""

    # Log with appropriate level
    if server_errors or client_errors:
        rp_client.log_message(summary, "ERROR")
    else:
        rp_client.log_message(summary, "INFO")

def _create_network_table(self, responses: list) -> str:
    """Create ASCII table for network requests."""
    # Header
    lines = [
        "┌" + "─" * 8 + "┬" + "─" * 60 + "┬" + "─" * 8 + "┬" + "─" * 12 + "┬" + "─" * 10 + "┐",
        "│ Method │ URL" + " " * 57 + "│ Status │ Duration (ms) │ Size (KB) │",
        "├" + "─" * 8 + "┼" + "─" * 60 + "┼" + "─" * 8 + "┼" + "─" * 12 + "┼" + "─" * 10 + "┤"
    ]

    # Rows (show all, not just 10)
    for r in responses:
        method = r.get('method', 'GET').ljust(6)
        url = r.get('url', '')[:58] + ("..." if len(r.get('url', '')) > 58 else "")
        url = url.ljust(58)
        status = str(r.get('status', '')).ljust(6)
        duration = f"{r.get('duration', 0):.2f}".rjust(10)
        size = f"{r.get('size', 0) / 1024:.1f}".rjust(8)

        lines.append(f"│ {method} │ {url} │ {status} │ {duration} │ {size} │")

    # Footer
    lines.append("└" + "─" * 8 + "┴" + "─" * 60 + "┴" + "─" * 8 + "┴" + "─" * 12 + "┴" + "─" * 10 + "┘")

    return "\n".join(lines)
```

#### تست:
- بررسی HAR file در Chrome DevTools
- بررسی console logs با errors/warnings/logs
- تست با بیش از 50 log
- بررسی formatting در ReportPortal

---

### **Phase 4: Scenario Independence - حذف Dependencies** 🔗
**زمان تخمینی:** 4-6 ساعت
**اولویت:** Critical

#### هدف:
هر scenario باید **مستقل** اجرا شود بدون وابستگی به سناریوهای قبلی

#### مشکل فعلی:
```gherkin
# PostBank applicant registration feature
الگوی سناریو: 1- به‌عنوان کارشناس حوزه باجه‌ها می‌خواهم متقاضی ثبت کنم
  با فرض کاربر در نقش کارشناس حوزه باجه ها قرار دارد  # ❌ این step login انجام می‌دهد
```

#### راه حل:

**4.1. اضافه کردن Background به همه features:**

```gherkin
# File: PostBank/features/sabte_motaghazi_*/sabte_motaghazi_*.feature

# language: fa
وِیژگی: ثبت متقاضی — ارسال برای تأیید جهت ایجاد باجه

  # ✅ اضافه شد
  زمینه:
    با فرض کاربر در صفحه "ورود" قرار دارد
    و کاربر با نقش "کارشناس حوزه باجه" وارد سیستم شده است

  الگوی سناریو: 1- به‌عنوان کارشناس حوزه باجه‌ها می‌خواهم متقاضی ثبت کنم
    # حالا login در Background انجام می‌شود
    با فرض کاربر در صفحه ثبت متقاضی قرار دارد
    ...
```

**4.2. Refactor login step definition:**

```python
# File: PostBank/features/steps/login_steps.py

@given('کاربر با نقش "{role}" وارد سیستم شده است')
def step_user_logged_in_with_role(context, role):
    """
    Generic step for logging in user with specific role.
    This replaces role-specific login steps.
    """
    # Get users with this role
    if hasattr(context, 'available_users') and context.available_users:
        role_users = [user for user in context.available_users
                     if user.get('نقش_سازمانی', '') == role
                     and user.get('فعال', '').strip().lower() == 'true']
    else:
        raise ValueError(f"No user data loaded. Check CSV file.")

    if not role_users:
        raise ValueError(f"No active users found with role: {role}")

    # Select random user
    selected_user = random.choice(role_users)
    context.current_user_data = selected_user

    # Perform login
    login_page = LoginPage(context.page, context.test_config)
    login_page.open()
    login_page.login(selected_user['نام_کاربری'], selected_user['رمز_عبور'])

    # Verify success
    dashboard_page = DashboardPage(context.page, context.test_config)
    dashboard_page.verify_page_loaded()

# ❌ حذف شود - دیگر لازم نیست
# @given('کاربر در نقش کارشناس حوزه باجه ها قرار دارد')
```

**4.3. Browser isolation بین scenarios:**

```python
# File: Nemesis/src/nemesis/infrastructure/environment/hooks.py

def before_scenario(context, scenario):
    """Setup before each scenario with browser isolation."""
    env_manager = getattr(context, "_env_manager", None)
    if not env_manager:
        return

    # Reset browser state for isolation
    if hasattr(context, 'page') and context.page:
        # Clear cookies
        context.page.playwright_page.context.clear_cookies()

        # Clear local storage
        context.page.playwright_page.evaluate("() => { localStorage.clear(); }")

        # Clear session storage
        context.page.playwright_page.evaluate("() => { sessionStorage.clear(); }")

    # Start scenario in reporting
    env_manager.before_scenario(context, scenario)
```

**4.4. Configuration:**

```yaml
# File: conf/behave.ini
[behave]
# Run scenarios in isolation
scenario_outline_annotation_schema = {name} -- @{row.id}

# Reset browser between scenarios
browser_isolation: true
clear_cookies: true
clear_storage: true
```

#### تست:
- اجرای تک‌تک scenarios به صورت مستقل
- اجرای scenarios به ترتیب تصادفی
- بررسی عدم تداخل state بین scenarios

---

### **Phase 5: PostBank Code Quality Improvements** 🧹
**زمان تخمینی:** 6-8 ساعت
**اولویت:** Medium

#### هدف:
1. Separation of Concerns - تفکیک data generation از page objects
2. حذف debug prints
3. ساده‌سازی step definitions

#### 5.1. Extract Data Generators:

**ایجاد ماژول جدید:**

```python
# File: PostBank/test_data/generators.py

"""Random test data generators for PostBank."""

import random
from datetime import datetime, timedelta
from typing import Dict, Any

class PersianDataGenerator:
    """Generate random Persian test data."""

    MALE_NAMES = [
        "علی", "محمد", "حسین", "رضا", "امیر", "مهدی", "سعید"
    ]

    FEMALE_NAMES = [
        "فاطمه", "زهرا", "مریم", "سارا", "نرگس", "الهام"
    ]

    LAST_NAMES = [
        "احمدی", "محمدی", "رضایی", "حسینی", "کریمی"
    ]

    @staticmethod
    def generate_national_code() -> str:
        """Generate valid Iranian national code with checksum."""
        # Generate 9 random digits
        digits = [random.randint(0, 9) for _ in range(9)]

        # Calculate checksum
        check_sum = 0
        for i in range(9):
            check_sum += digits[i] * (10 - i)

        remainder = check_sum % 11
        check_digit = remainder if remainder < 2 else 11 - remainder

        return ''.join(map(str, digits)) + str(check_digit)

    @staticmethod
    def generate_birth_date(min_age: int = 18, max_age: int = 65) -> str:
        """Generate random birth date (Jalali format)."""
        # Calculate date range
        today = datetime.now()
        min_date = today - timedelta(days=max_age * 365)
        max_date = today - timedelta(days=min_age * 365)

        # Random date in range
        random_days = random.randint(0, (max_date - min_date).days)
        birth_date = min_date + timedelta(days=random_days)

        # Convert to Jalali (simplified - use jdatetime library)
        # For now, return Gregorian
        return birth_date.strftime("%Y/%m/%d")

    @classmethod
    def generate_person(cls, gender: str = "male") -> Dict[str, Any]:
        """Generate random person data."""
        if gender == "male":
            first_name = random.choice(cls.MALE_NAMES)
        else:
            first_name = random.choice(cls.FEMALE_NAMES)

        last_name = random.choice(cls.LAST_NAMES)

        return {
            "first_name": first_name,
            "last_name": last_name,
            "national_code": cls.generate_national_code(),
            "birth_date": cls.generate_birth_date(),
            "gender": gender,
            "full_name": f"{first_name} {last_name}"
        }
```

**5.2. Refactor Page Object:**

```python
# File: PostBank/pages/applicant_registration_page.py

# ❌ حذف شود - 300 خط data generation
# def _generate_random_personal_data(self) -> dict:
#     ...

# ✅ استفاده از generator
from test_data.generators import PersianDataGenerator

class ApplicantRegistrationPage(BasePage):

    def fill_applicant_form(self, data: dict = None) -> None:
        """Fill applicant registration form.

        Args:
            data: Optional dict with form data. If None, generates random data.
        """
        if data is None:
            # Generate random data
            data = PersianDataGenerator.generate_person(gender="male")

        # Fill form fields
        self.fill_first_name(data['first_name'])
        self.fill_last_name(data['last_name'])
        self.fill_national_code(data['national_code'])
        self.fill_birth_date(data['birth_date'])
        # ...
```

**5.3. حذف Debug Prints:**

```python
# File: PostBank/features/steps/*.py

# ❌ حذف شود
# print(f"DEBUG: Selected user = {selected_user}")
# print(f"DEBUG: Current user data = {context.current_user_data}")

# ✅ جایگزینی با logging
import logging
logger = logging.getLogger(__name__)

@given('...')
def step_impl(context):
    logger.debug(f"Selected user: {selected_user}")
    logger.debug(f"Current user data: {context.current_user_data}")
```

**5.4. Simplify Step Definitions:**

```python
# File: PostBank/features/steps/login_steps.py

def _get_username_from_context(context, param_value: str) -> str:
    """Extract username with priority: active_outline > current_user_data > parameter."""
    # Priority 1: active_outline
    if hasattr(context, 'active_outline') and context.active_outline:
        username = context.active_outline.get('نام_کاربری', '')
        if username:
            return username

    # Priority 2: current_user_data
    if hasattr(context, 'current_user_data') and context.current_user_data:
        username = context.current_user_data.get('نام_کاربری', '')
        if username:
            return username

    # Priority 3: parameter value
    return param_value

@when('کاربر نام کاربری "{نام_کاربری}" را وارد می‌کند')
def step_user_enters_username(context, نام_کاربری):
    """User enters username."""
    username = _get_username_from_context(context, نام_کاربری)
    context.login_page.enter_username(username)

    # Store for later
    if not hasattr(context, 'current_user_data'):
        context.current_user_data = {}
    context.current_user_data['نام_کاربری'] = username
```

#### تست:
- تست data generators با 100 نمونه
- بررسی عدم debug prints در output
- بررسی عملکرد step definitions

---

### **Phase 6: Stack Trace & Error Enhancement** 🐛
**زمان تخمینی:** 3-4 ساعت
**اولویت:** Medium

#### هدف:
1. Stack traces کامل (بدون truncation)
2. خطاها به صورت واضح زیر step نمایش داده شوند
3. Context information در error logs

#### 6.1. Remove Stack Trace Truncation:

```python
# File: Nemesis/src/nemesis/reporting/report_portal/rp_logger.py

def log_exception(self, exception: Exception, description: str = "") -> None:
    """Log exception with FULL stack trace (no truncation)."""
    item_id = self._get_current_item_id()

    exception_type = type(exception).__name__
    exception_message = str(exception)
    stack_trace = RPUtils.extract_stack_trace(exception)

    # ❌ حذف شود
    # if len(full_message) > 15000:
    #     full_message = full_message[:15000] + "\n\n... [truncated]"

    # ✅ ارسال کامل
    full_message = f"""{description}

EXCEPTION: {exception_type}
Message: {exception_message}

Stack Trace:
{stack_trace}

Time: {RPUtils.timestamp()}"""

    # Log to ReportPortal
    try:
        self.client.log(
            time=RPUtils.timestamp(),
            message=full_message,
            level="ERROR",
            item_id=item_id,
        )
    except Exception as e:
        # If too large, attach as file instead
        self._logger.warning(f"Stack trace too large for log, attaching as file: {e}")
        self.attach_file(
            full_message.encode('utf-8'),
            "Full Stack Trace",
            "text/plain"
        )
```

**6.2. Add Context to Errors:**

```python
# File: Nemesis/src/nemesis/utils/decorators/exception_handler.py

def handle_exceptions(
    *,
    include_context: bool = True,  # ✅ جدید
    **kwargs
) -> Callable[[F], F]:
    """Decorator with context information."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except catch_exceptions as e:
                # Build error message with context
                error_parts = [f"Exception in {actual_module}.{func.__name__}"]

                if include_context:
                    # Add function arguments
                    error_parts.append(f"Arguments: {args[:3]}")  # First 3 args
                    error_parts.append(f"Kwargs: {kwargs}")

                error_msg = "\n".join(error_parts)

                # Log with traceback
                log_kwargs = {
                    "module": actual_module,
                    "method": func.__name__,
                }

                if include_traceback:
                    log_kwargs["traceback"] = tb.format_exc()

                log_method(error_msg, **log_kwargs)

                # Re-raise or return default
                if reraise:
                    raise
                return default_return

        return wrapper
    return decorator
```

**6.3. Step-level Error Context:**

```python
# File: Nemesis/src/nemesis/infrastructure/environment/hooks.py

def after_step(context, step):
    """After step hook with error context."""
    env_manager = getattr(context, "_env_manager", None)
    if not env_manager:
        return

    # Check if step failed
    if step.status == "failed":
        # Get error from step
        if hasattr(step, 'exception') and step.exception:
            # Add context information
            context_info = {
                "step_name": step.name,
                "step_keyword": step.keyword,
                "scenario_name": context.scenario.name if hasattr(context, 'scenario') else "Unknown",
                "feature_name": context.feature.name if hasattr(context, 'feature') else "Unknown",
                "line_number": step.line if hasattr(step, 'line') else "Unknown",
            }

            # Log to ReportPortal with context
            reporter = env_manager.reporting_env._reporter_manager
            if reporter.is_rp_enabled():
                rp_client = reporter.get_rp_client()

                context_msg = f"""
Step Failed: {context_info['step_name']}
Feature: {context_info['feature_name']}
Scenario: {context_info['scenario_name']}
Line: {context_info['line_number']}
"""
                rp_client.log_message(context_msg, "ERROR")
                rp_client.log_exception(step.exception, context_msg)

    # Continue with normal after_step
    env_manager.after_step(context, step)
```

#### تست:
- تست با long stack traces (> 15000 chars)
- بررسی context information در error logs
- تست با nested exceptions

---

## 📊 اولویت‌بندی اجرا

### موج اول (Week 1) - Critical Fixes:
1. **Phase 1**: Action Logging Enhancement (4-6h)
2. **Phase 2**: Performance Metrics as Attributes (6-8h)
3. **Phase 4**: Scenario Independence (4-6h)

**تخمین کل:** 14-20 ساعت

### موج دوم (Week 2) - Enhancements:
4. **Phase 3**: Console & Network Logs Readability (5-7h)
5. **Phase 6**: Stack Trace & Error Enhancement (3-4h)

**تخمین کل:** 8-11 ساعت

### موج سوم (Week 3) - Code Quality:
6. **Phase 5**: PostBank Code Quality (6-8h)

**تخمین کل:** 6-8 ساعت

---

## ✅ تست پلن

### Unit Tests:
- `test_action_logging.py` - تست action logger با element details
- `test_metrics_attributes.py` - تست ارسال metrics به صورت attributes
- `test_console_formatting.py` - تست formatting console logs
- `test_network_har.py` - تست HAR format export
- `test_scenario_isolation.py` - تست browser isolation

### Integration Tests:
- `test_reportportal_integration.py` - تست کامل با ReportPortal
- `test_postbank_scenarios.py` - تست independence سناریوها

### E2E Tests:
- اجرای کامل test suite PostBank
- بررسی ReportPortal UI
- تست performance با attributes

---

## 📝 Checklist نهایی

- [ ] Action logs شامل element tag name
- [ ] Performance metrics به صورت ReportPortal attributes
- [ ] Console logs خوانا و کامل
- [ ] Network logs در فرمت HAR
- [ ] سناریوها مستقل (بدون dependency)
- [ ] Browser state isolated بین scenarios
- [ ] Stack traces کامل (بدون truncation)
- [ ] Debug prints حذف شده
- [ ] Data generators جدا از page objects
- [ ] Step definitions ساده‌سازی شده
- [ ] همه تست‌ها پاس می‌کنند
- [ ] Documentation بروز شده

---

## 🎓 نکات مهم

1. **Backward Compatibility**: همه تغییرات باید backward compatible باشند
2. **Configuration**: همه ویژگی‌های جدید قابل configure باشند
3. **Testing**: هر phase باید قبل از merge کامل تست شود
4. **Documentation**: هر تغییر باید document شود

---

**تاریخ ایجاد:** 2025-12-23
**نسخه:** 1.0
**وضعیت:** آماده برای تأیید و اجرا

✅ **استانداردسازی و یکپارچه‌سازی سیستم لاگینگ Nemesis با SigNoz**
✅ **هدف اصلی:**

✅ تمام لاگ‌ها (framework و test execution) در یک فرمت استاندارد تولید شوند، context کامل داشته باشند، severity هماهنگ شود، با reliability بالا به SigNoz ارسال شوند. کانال‌ها و سطح لاگ قابل تنظیم باشند و ریپو تست فقط لاگ تست را تولید کند.

✅ **1️⃣ Task اصلی: طراحی و پیاده‌سازی Centralized Logging Engine**

✅ **Objective:**

✅ همه لاگ‌ها از یک نقطه مرکزی عبور کنند

✅ فرمت لاگ یکسان و استاندارد باشد

✅ Context کامل (Correlation ID, Execution ID, Test/Framework Context) در همه لاگ‌ها وجود داشته باشد

✅ قابلیت ارسال لاگ به چندین کانال (Local, SigNoz، Elastic یا کانال‌های آینده) وجود داشته باشد

✅ **Subtasks:**

✅ تعریف فرمت استاندارد لاگ (timestamp, level, message, correlation_id, execution_id, context, thread_id, process_id, module, service_name, operation_type)

✅ پیاده‌سازی Context Propagation و Correlation ID generation برای تمام ماژول‌ها

✅ پیاده‌سازی Severity Mapping استاندارد برای Exceptionهای مختلف

✅ ایجاد قابلیت انتخاب کانال ارسال لاگ به صورت Configurable

✅ تضمین batch shipping و retry logic برای reliability بالا

✅ **2️⃣ Task: استانداردسازی لاگ‌های اجرای تست (Test Execution Logs)**

✅ **Objective:**

✅ لاگ‌های اجرای تست کاملاً جدا و مستقل از لاگ‌های internal framework باشند

✅ لاگ‌های تست به کانال تست (SigNoz یا Local) ارسال شوند

✅ فرمت و context لاگ تست مطابق استاندارد Central Logger باشد

✅ **Subtasks:**

✅ تعریف Service Name مخصوص تست (مثلاً test-execution)

✅ Propagate کردن test-specific context (test_id, scenario, browser, start_time)

✅ تعیین سطح لاگ پیش‌فرض برای تست (INFO یا DEBUG configurable)

✅ امکان کانفیگ channel فعال برای تست (مثلاً فقط SigNoz یا فقط Local)

✅ اطمینان از اینکه ریپو تست فقط لاگ تست تولید کند و framework logs را شامل نشود

✅ **3️⃣ Task: استانداردسازی لاگ‌های داخلی فریمورک (Internal Framework Logs)**

✅ **Objective:**

✅ لاگ‌های internal framework با همان Central Logger مدیریت شوند

✅ Context کامل framework در همه لاگ‌ها موجود باشد

✅ قابلیت ارسال به چندین کانال به صورت Configurable

✅ **Subtasks:**

✅ تعریف Service Name مخصوص framework (مثلاً nemesis-framework)

✅ Propagate کردن framework-specific context (module, thread_id, process_id)

✅ تعیین log level پیش‌فرض برای framework logs (DEBUG یا INFO configurable)

✅ اطمینان از اینکه framework logs با test logs مخلوط نشوند

✅ ارسال reliable با retry و batch برای همه کانال‌ها

✅ **4️⃣ Task: Configurable Channels و Log Levels**

✅ **Objective:**

✅ قابلیت فعال/غیرفعال کردن هر channel و تنظیم سطح لاگ برای هر channel

✅ Channelها باید مستقل و قابل توسعه باشند

✅ **Subtasks:**

✅ تعریف کانفیگ برای Local, SigNoz و کانال‌های آینده

✅ امکان تعیین log level برای هر کانال (DEBUG, INFO, WARNING, ERROR, CRITICAL)

✅ تضمین propagation context و severity mapping در تمام کانال‌ها

✅ امکان افزودن کانال جدید بدون تغییر Core Logger

✅ مدیریت conflict بین channelها (مثلاً service name و context همسان)

✅ **5️⃣ Task: Reliability و Observability**

✅ **Objective:**

✅ جلوگیری از Race Condition و Missing Log

✅ تضمین ارسال لاگ حتی در صورت failure جزئی

✅ ارائه feedback برای failures

✅ **Subtasks:**

✅ Implement batch shipping برای SigNoz و کانال‌های دیگر

✅ Implement retry logic برای failed shipments

✅ Logging داخلی برای failed shipments و retry attempts

✅ شناسایی و حل potential race conditions

✅ تضمین consistency و traceability در SigNoz Dashboard

✅ **6️⃣ Task: Documentation و Test**

✅ **Objective:**

✅ مستندسازی کامل طراحی و کانفیگ

✅ تست صحت فرمت، context و severity لاگ‌ها

✅ **Subtasks:**

✅ مستندسازی فرمت استاندارد لاگ و هر فیلد آن

✅ ارائه مثال از log تست و log فریمورک

✅ نوشتن Unit Test برای:

✅ Propagation context

✅ Severity mapping

✅ Channel selection

✅ Retry logic

✅ تست یکپارچگی با SigNoz و Local channel

✅ ارائه دستورالعمل کانفیگ برای توسعه‌دهندگان

✅ **Notes / Constraints:**

✅ همه لاگ‌ها باید سمت Nemesis باشند

✅ ریپو تست فقط لاگ‌های تست را تولید کند

✅ Channels و log levels کاملاً قابل کانفیگ باشند

✅ قابلیت افزودن کانال جدید بدون تغییر Core Logger فراهم شود
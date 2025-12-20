1️⃣ Domain-Driven Design (DDD) Compliance

1.1 Domain Identification

☐ Core Domain به‌صورت صریح شناسایی شده است

☐ Subdomainها (Core / Supporting / Generic) مشخص هستند

☐ Business Logic داخل Domain Layer متمرکز است، نه در Controller یا Infrastructure

☐ Domain Model مستقل از Framework و Persistence است

1.2 Layer Separation

☐ Domain Layer فقط شامل Entity / Value Object / Domain Service / Repository Interface است

☐ Application Layer شامل Use Case / Application Service است (Orchestration، نه Logic دامنه)

☐ Infrastructure Layer شامل DB، ORM، Messaging، External APIs است

☐ هیچ Logic دامنه‌ای در Infrastructure یا UI وجود ندارد

1.3 Dependency Direction

☐ Dependencyها فقط به سمت داخل هستند (Outer → Inner)

☐ Domain به هیچ لایه‌ای وابسته نیست

☐ Application به Infrastructure وابستگی مستقیم ندارد (Dependency Inversion رعایت شده)

☐ Interfaceها در لایه داخلی تعریف شده‌اند، Implementation در بیرون

2️⃣ Clean Architecture Compliance

2.1 Boundary Definition

☐ Boundary بین Domain / Application / Infrastructure شفاف و قابل تشخیص است

☐ Use Caseها مرز اصلی سیستم هستند

☐ Data crossing boundaries از طریق DTO / Contract انجام می‌شود

☐ Leakage مفهومی بین لایه‌ها وجود ندارد

2.2 Framework & Tool Placement

☐ Framework (Django, Spring, Flask, FastAPI, ORM, etc.) در لایه Infrastructure یا Delivery است

☐ Framework در Domain Layer import نشده است

☐ Business Rule بدون نیاز به Framework قابل اجرا و تست است

☐ تعویض Framework بدون تغییر Domain ممکن است

3️⃣ SOLID Compliance (Focus on SRP)

3.1 Single Responsibility Principle

☐ هر Class دقیقاً یک Reason to Change دارد

☐ Entityها فقط مسئول State و Invariant خود هستند

☐ Serviceها بیش از یک concern را پوشش نمی‌دهند

☐ God Object وجود ندارد

3.2 Other SOLID Signals

☐ Open/Closed: رفتار جدید بدون تغییر کد موجود قابل اضافه‌شدن است

☐ Liskov: Subtypeها رفتار Contract را نمی‌شکنند

☐ Interface Segregation: Interfaceهای کوچک و هدفمند هستند

☐ Dependency Inversion: High-level policy به low-level detail وابسته نیست

4️⃣ Clean Code Quality

4.1 Naming (Intent-Revealing)

☐ نام Class و Method بیانگر چرایی است نه فقط چگونگی

☐ Abbreviation مبهم وجود ندارد

☐ Naming دامنه‌محور است، نه تکنیکال

☐ Verb/Noun در Method و Class رعایت شده است

4.2 Size & Complexity

☐ Classها کوچک و متمرکز هستند

☐ Methodها کوتاه، خوانا و single-purpose هستند

☐ Cyclomatic Complexity قابل‌قبول است

☐ Nested conditionهای عمیق وجود ندارد

4.3 Coupling & Cohesion

☐ Coupling پایین بین ماژول‌ها وجود دارد

☐ Cohesion درون هر ماژول بالاست

☐ Circular Dependency وجود ندارد

☐ تغییر در یک ماژول، ripple effect غیرمنطقی ایجاد نمی‌کند

5️⃣ Code Smells & Technical Debt

☐ Duplication قابل‌توجه وجود ندارد

☐ Primitive Obsession شناسایی و حذف شده

☐ Feature Envy وجود ندارد

☐ Dead Code یا Comment-Driven Code وجود ندارد

☐ TODO/FIXME بحرانی بدون Ticket یا Owner نیست

☐ Debt ثبت، آگاهانه و قابل پرداخت است

📌 Final Acceptance Rule

Definition of Done = TRUE
فقط در صورتی که هیچ Blocker معماری وجود نداشته باشد و موارد Fail در Core Domain صفر باشند.
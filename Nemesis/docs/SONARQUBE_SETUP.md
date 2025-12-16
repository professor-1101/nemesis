# راهنمای راه‌اندازی SonarQube برای Nemesis

این راهنما روش‌های مختلف استفاده از SonarQube برای تحلیل کیفیت کد پروژه Nemesis را توضیح می‌دهد.

## روش 1: SonarCloud (پیشنهادی - رایگان)

SonarCloud یک سرویس ابری رایگان است که نیازی به نصب سرور ندارد.

### مراحل راه‌اندازی:

1. **ثبت‌نام در SonarCloud**
   - به https://sonarcloud.io بروید
   - با GitHub/GitLab/Bitbucket ثبت‌نام کنید
   - یک سازمان (Organization) ایجاد کنید

2. **دریافت Token**
   ```bash
   # بعد از لاگین، از Settings > Security > Generate Token یک token بگیرید
   ```

3. **تنظیم پروژه**
   - از داشبورد SonarCloud، پروژه جدید ایجاد کنید
   - Project Key را کپی کنید

4. **اجرای تحلیل**
   ```bash
   # نصب sonar-scanner (برای Windows)
   # دانلود از: https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/
   # یا استفاده از Docker:
   
   docker run --rm \
     -v "%cd%:/usr/src" \
     -w /usr/src \
     sonarsource/sonar-scanner-cli:latest \
     -Dsonar.projectKey=nemesis-automation \
     -Dsonar.organization=your-org-key \
     -Dsonar.sources=src \
     -Dsonar.host.url=https://sonarcloud.io \
     -Dsonar.login=YOUR_TOKEN
   ```

## روش 2: SonarQube Local Server

### پیش‌نیازها:
- Java 17+
- Docker (اختیاری)

### نصب با Docker:

```bash
# راه‌اندازی SonarQube Server
docker run -d \
  --name sonarqube \
  -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
  sonarqube:community

# دسترسی به پنل: http://localhost:9000
# Username: admin
# Password: admin (باید در اولین ورود تغییر دهید)
```

### نصب Sonar Scanner:

1. **دانلود Sonar Scanner**
   ```powershell
   # دانلود از: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
   # یا با Chocolatey:
   choco install sonarscanner-msbuild-net46
   ```

2. **اضافه کردن به PATH**
   ```powershell
   # اضافه کردن مسیر sonar-scanner\bin به PATH
   $env:PATH += ";C:\path\to\sonar-scanner\bin"
   ```

### اجرای تحلیل:

```bash
cd Projects/Nemesis

# تنظیم token (از SonarQube UI)
# Settings > My Account > Security > Generate Token

# اجرای تحلیل
sonar-scanner \
  -Dsonar.projectKey=nemesis-automation \
  -Dsonar.sources=src \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=YOUR_TOKEN
```

## روش 3: استفاده از GitHub Actions

اگر از GitHub استفاده می‌کنید، فایل `.github/workflows/sonarcloud.yml` آماده است.

1. **تنظیم Secrets در GitHub**
   - Settings > Secrets > Actions
   - اضافه کردن `SONAR_TOKEN`

2. **Push به GitHub**
   - با هر push به branch اصلی، تحلیل خودکار انجام می‌شود

## ابزارهای پیشنهادی برای Python

برای تحلیل بهتر، این ابزارها را نصب کنید:

```bash
pip install pylint bandit mypy pytest-cov safety

# اجرای تحلیل‌ها
pylint src/nemesis --output-format=text > pylint-report.txt
bandit -r src/nemesis -f json -o bandit-report.json
mypy src/nemesis
pytest --cov=src/nemesis --cov-report=xml
```

## تنظیمات فایل sonar-project.properties

فایل `sonar-project.properties` در ریشه پروژه ایجاد شده است و می‌توانید آن را سفارشی کنید.

### نکات مهم:

- **Exclusions**: فولدرهای غیر ضروری (__pycache__, build, dist) حذف شده‌اند
- **Sources**: فقط `src` به‌عنوان source code در نظر گرفته شده
- **Tests**: اگر تست‌ها دارید، در فولدر `tests` قرار دهید

## نتایج و گزارش‌ها

بعد از اجرای تحلیل، می‌توانید:

1. گزارش‌ها را در SonarQube/SonarCloud مشاهده کنید
2. Quality Gate را بررسی کنید
3. Code Smells، Bugs، و Security Hotspots را ببینید
4. Coverage را بررسی کنید (اگر تست‌ها coverage داشته باشند)

## دستورات سریع

```bash
# SonarCloud با Docker
docker run --rm \
  -v "${PWD}:/usr/src" \
  -w /usr/src \
  -e SONAR_TOKEN=YOUR_TOKEN \
  sonarsource/sonar-scanner-cli:latest

# SonarQube Local
sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.login=YOUR_TOKEN
```

## لینک‌های مفید

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [SonarQube Python Plugin](https://docs.sonarqube.org/latest/analyzing-source-code/languages/python/)
- [Sonar Scanner CLI](https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/)


# 🏫 Uganda School Management System
### A Complete Django-Based School ERP for Secondary Schools

---

## ✨ Features

| Module | Features |
|--------|---------|
| 👨‍🎓 **Students** | Register, search, edit, ID cards, promotions, CSV export |
| 💰 **Fees** | Fee structures, payment recording, official receipts, defaulters list |
| 📊 **Results** | Exam creation, mark entry grid, report cards, subject analysis |
| 📋 **Requirements** | Term supplies tracking per student per class |
| 📈 **Reports** | Enrollment, fees, academic performance, CSV exports |
| 🔐 **Security** | Per-class password protection, role-based user accounts |
| ⚙️ **Settings** | Fully customizable school name, logo, grading scale, currency |

---

## 🚀 Quick Start (3 Steps)

### Step 1 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Initialize Database
```bash
python manage.py makemigrations
python manage.py migrate
python setup.py
```

### Step 3 — Run Server
```bash
python manage.py runserver
```
Open your browser: **http://127.0.0.1:8000/**

---

## 🔑 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `admin@2024` |
| Bursar | `bursar` | `bursar@2024` |
| Director of Studies | `dos` | `dos@2024` |
| Head Teacher | `headteacher` | `head@2024` |
| Teacher | `teacher1` | `teacher@2024` |

## 🔒 Default Class Passwords (for Results Access)
```
S1 = s12024    S2 = s22024    S3 = s32024
S4 = s42024    S5 = s52024    S6 = s62024
```
> Change these immediately in **Dashboard → Classes → Manage Classes**

---

## 📁 Project Structure
```
sms/
├── manage.py
├── setup.py              ← Run once to seed database
├── requirements.txt
├── db.sqlite3            ← Created automatically
├── school_mgmt/          ← Django project config
│   ├── settings.py
│   └── urls.py
├── apps/
│   ├── core/             ← School settings, classes, subjects, users
│   ├── students/         ← Student registration & management
│   ├── fees/             ← Fee structures, payments, receipts
│   ├── results/          ← Exams, marks, report cards
│   ├── requirements/     ← Term requirements tracking
│   └── reports/          ← Analytics & reports
├── templates/            ← All HTML templates
│   ├── base/             ← Layout, dashboard, settings, classes
│   ├── auth/             ← Login, users, profile
│   ├── students/
│   ├── fees/
│   ├── results/
│   ├── requirements/
│   └── reports/
├── static/               ← CSS, JS, images
└── media/                ← Uploaded photos & logos
```

---

## 🇺🇬 Uganda-Specific Features

### Subjects Available
O-Level: History, Chemistry, Biology, Fine Art, Geography, Mathematics, English,
ICT, Luganda, Kiswahili, Physics, Agriculture, CRE, Food & Nutrition, Literature

A-Level: Economics, Accounting, Entrepreneurship, General Paper, Subsidiary ICT

### Classes
O-Level: S1, S2, S3, S4
A-Level: S5, S6

### UNEB-Style Grading (Customizable)
| Grade | Points | Default Range | Label |
|-------|--------|---------------|-------|
| A | 1 | 80–100% | Distinction |
| B | 2 | 70–79% | Merit |
| C | 3 | 60–69% | Credit |
| D | 4 | 50–59% | Pass |
| E | 5 | 40–49% | Pass |
| F | 6 | 30–39% | Fail |
| U | 9 | 0–29% | Ungraded |

> Aggregate is computed as sum of best 8 subject points (UNEB O-level standard)

---

## 📱 Desktop & Mobile App

You can wrap this web app into a **desktop application** using:

### Option A — PyInstaller + WebView (Desktop App)
```bash
pip install pywebview pyinstaller

# Create run_app.py:
import webview, threading, subprocess

def start_django():
    subprocess.run(['python', 'manage.py', 'runserver', '--noreload'])

threading.Thread(target=start_django, daemon=True).start()
webview.create_window('School Management System', 'http://127.0.0.1:8000', width=1400, height=900)
webview.start()

# Package:
pyinstaller --onefile --windowed run_app.py
```

### Option B — Electron (Cross-platform Desktop)
```bash
npm init -y
npm install electron
# Create main.js pointing to http://localhost:8000
electron .
```

### Option C — Mobile App (Android/iOS)
Use **Capacitor** or **Cordova** to wrap the web app:
```bash
npm install -g @capacitor/cli
cap init SchoolSMS com.school.sms
cap add android
cap open android
```

### Option D — Progressive Web App (PWA)
The app already works great on mobile browsers.
Add to home screen on Android/iOS for app-like experience.

---

## ⚙️ Customization

### Change School Name & Logo
Go to **Dashboard → School Settings** and update:
- School name, motto, address, phone, email
- Upload school logo
- Set grading scale boundaries
- Set current term and year
- Change currency (default: UGX)

### Add Custom Subjects
Go to **Dashboard → Subjects → Add Subject**

### Add More Classes / Streams
Go to **Dashboard → Classes → Add Class**
Example: S5 Science, S5 Arts, S6 Science, S6 Arts

### Change Class Passwords
Go to **Dashboard → Classes** → click Update Password

---

## 🛡️ Production Deployment

For production use:

```python
# school_mgmt/settings.py
DEBUG = False
SECRET_KEY = 'your-very-long-random-secret-key'
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Use PostgreSQL for production:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'schooldb',
        'USER': 'schooluser',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

```bash
pip install gunicorn
python manage.py collectstatic
gunicorn school_mgmt.wsgi:application --bind 0.0.0.0:8000
```

Use **Nginx** as a reverse proxy in front of Gunicorn.

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `No module named django` | Run `pip install -r requirements.txt` |
| Images not showing | Run `python manage.py collectstatic` |
| `OperationalError: no such table` | Run `python manage.py migrate` |
| Forgot admin password | `python manage.py changepassword admin` |
| Port 8000 in use | `python manage.py runserver 8080` |

---

## 📞 Support
Built specifically for Uganda Secondary Schools.
Customize for your school in **Settings → School Settings**.

© 2024 Uganda School Management System

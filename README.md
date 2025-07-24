# PredictiveMaint

pip install mssql-django

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'PM',  # Your local database name
        'USER': 'sa',  # Your SQL Server username
        'PASSWORD': 'admin@123',  # Your SQL Server password
        'HOST': 'localhost',  # Use 'localhost' or '127.0.0.1' for local DB
        'PORT': '1433',  # Default SQL Server port
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
        },
    }
}

python manage.py makemigrations
python manage.py migrate

# 🔧 Predictive Maintenance Portal – Django Application

This project is a **Django-based web portal** developed for **Predictive Maintenance** of industrial equipment. It helps monitor, analyze, and visualize equipment data in real-time or near real-time, with integration for offline JavaScript, Bootstrap, and PLC/IIoT data interfaces.
---
## 📁 Project Structure

predictive_maintenance/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── .env (optional)
├── static/
│ └── js/
│ ├── jquery-3.6.0.min.js
│ ├── jquery.validate.min.js
│ └── bootstrap.bundle.min.js
├── templates/
│ └── base.html
├── predictive_maintenance/
│ ├── init.py
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
└── app_name/
├── init.py
├── admin.py
├── apps.py
├── models.py
├── views.py
├── urls.py
└── templates/
└── app_name/



## 🚀 Quick Start – Setup Guide

### 📌 Prerequisites

- Python 3.12+
- pip
- virtualenv (optional but recommended)
- Git

---

### 🔧 Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/predictive-maintenance.git
cd predictive-maintenance
🐍 Step 2: Create & Activate Virtual Environment

python -m venv venv
# Activate (Linux/macOS)
source venv/bin/activate
# Activate (Windows)
venv\Scripts\activate
📦 Step 3: Install Dependencies

pip install -r requirements.txt
📄 Example requirements.txt:


Django>=4.0
python-decouple
psycopg2-binary  # If using PostgreSQL
⚙️ Step 4: Setup Django Project

python manage.py migrate
python manage.py createsuperuser
▶️ Step 5: Run Development Server

python manage.py runserver
Open your browser: http://127.0.0.1:8000

🧪 Admin Panel Access
URL: http://127.0.0.1:8000/admin/

Use superuser credentials created in Step 4.

🌐 Offline JavaScript Setup (Bootstrap + jQuery)
All JS files are served from local /static/js/ path.

✅ Example (in base.html or your template):

{% load static %}

<!-- jQuery Core -->
<script src="{% static 'js/jquery-3.6.0.min.js' %}"></script>

<!-- jQuery Validation -->
<script src="{% static 'js/jquery.validate.min.js' %}"></script>

<!-- Bootstrap Bundle with Popper -->
<script src="{% static 'js/bootstrap.bundle.min.js' %}"></script>
Ensure static folder is properly configured in your settings.py.

🔐 .env File (Optional)
Create a .env in your root project folder:


DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost
⚙️ settings.py Key Static Config

STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]
📊 Features
Admin dashboard to configure machines

PLC tag management

Data visualization (charts, tables)

Offline Bootstrap 5 & jQuery

Shift-wise and production-wise report generation

Error and downtime tracking

Modular app structure for future expansion (CBM)

🔌 API / PLC Integration (Optional Modules)
OPC UA or MQTT tag data fetching (Python-based microservices)

Gateway/Edge integration with Siemens IOT2050

Raw data posting to PostgreSQL or external DLK API

Scheduled background tasks (Celery or CRON-based)

🔒 Security Tips (for Production)

Set DEBUG=False

Use strong SECRET_KEY

Set up ALLOWED_HOSTS

Use HTTPS and secure headers

Serve static files via Nginx





🧑‍💻 Developer
Akash T S
Centre of Excellence,
Titan Engineering & Automation Ltd.
📞 +91 9008699748
📧 akashadi@titan.co.in
# Attendance System

A Django-based employee attendance management application with optional face profile support.

---
📖 **[View System Manual](SYSTEM_MANUAL.md)**
---

## 🚀 Key Features

- Employee management (CRUD)
- Check-in/Check-out attendance tracking
- Department management
- Reports (attendance history and summaries)
- User login + admin interface
- Django templates, static JS/CSS for UI
- Responsive web UI (mobile/tablet/desktop) with collapsible sidebar and mobile overlay support


## 🧩 Prerequisites

- Python 3.10
- pip
- git

## 🛠️ Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/Fr4udgrammer/attendance_system.git
   cd attendance_system
   ```

2. Create and activate virtual environment:
   - Windows:
     ```bash
     python -m venv .venv310
     .venv310\Scripts\activate
     ```
   - Linux/macOS:
     ```bash
     python -m venv .venv310
     source .venv310/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Create superuser (optional but recommended):
   ```bash
   python manage.py createsuperuser
   ```

6. Run server:
   ```bash
   python manage.py runserver
   ```

7. Open in browser:
   - `http://127.0.0.1:8000/`
   - `http://127.0.0.1:8000/admin`

## 🔗 Important URLs

- `/login`
- `/dashboard`
- `/attendance/checkin`
- `/attendance/list`
- `/employees/list`
- `/employees/add`
- `/employees/edit/<id>`
- `/departments/list`
- `/departments/add`
- `/reports/list`

## 📁 Core folders

- `apps/accounts`
- `apps/employees`
- `apps/attendance`
- `apps/reports`
- `templates/`
- `static/`
- `attendance_system/settings.py`
- `manage.py`

## 🧪 Extra commands

- Seed initial data:
  ```bash
  python manage.py setup_initial_data
  ```

## 💡 Recommendations

- Use a clean SQLite file for each environment: remove `db.sqlite3` and recreate migrations when needed.
- Add tests and run `python manage.py test`.
- Enforce linting with tools like `flake8` and formatting with `black`.

## 📦 Docker (example)

1. `Dockerfile` example:
   ```Dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   COPY requirements.txt ./
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   RUN python manage.py migrate
   EXPOSE 8000
   CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
   ```

2. Build and run:
   ```bash
   docker build -t attendance_system .
   docker run -p 8000:8000 attendance_system
   ```

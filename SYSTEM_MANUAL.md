# Attendance System - System Manual

Welcome to the **Attendance System** manual. This document provides a comprehensive guide to installing, configuring, and using the system.

## Table of Contents
1. [Introduction](#introduction)
2. [Hardware & Software Requirements](#hardware--software-requirements)
3. [Installation & Setup](#installation--setup)
4. [System Architecture](#system-architecture)
5. [Modules & Features](#modules--features)
    - [Accounts & Security](#accounts--security)
    - [Employee Management](#employee-management)
    - [Attendance Tracking](#attendance-tracking)
    - [Reporting](#reporting)
6. [Administrator Guide](#administrator-guide)
7. [User Guide](#user-guide)
8. [Troubleshooting](#troubleshooting)

---

## Introduction
The Attendance System is a Django-based web application designed to help organizations manage employee attendance efficiently. It supports core HR functions including employee record management, department organization, shift scheduling, and attendance tracking with optional face recognition support.

## Hardware & Software Requirements
- **Operating System:** Windows, Linux, or macOS.
- **Python:** Version 3.10 or higher.
- **Database:** SQLite (default), but compatible with PostgreSQL/MySQL.
- **Optional:** Webcam for face-recognition-based check-in.

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Fr4udgrammer/attendance_system.git
cd attendance_system
```

### 2. Environment Setup
Create and activate a virtual environment:
- **Windows:**
  ```bash
  python -m venv .venv310
  .venv310\Scripts\activate
  ```
- **Unix/macOS:**
  ```bash
  python -m venv .venv310
  source .venv310/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Configuration
Apply migrations to set up the database schema:
```bash
python manage.py migrate
```

### 5. Initial Data (Optional)
Seed the database with initial configurations and sample data:
```bash
python manage.py setup_initial_data
```

### 6. Create Superuser
To access the admin panel:
```bash
python manage.py createsuperuser
```

### 7. Run the Application
```bash
python manage.py runserver
```
Access the system at `http://127.0.0.1:8000/`.

---

## System Architecture
The application follows the Model-View-Template (MVT) pattern and is modularized into several Django apps:
- **`apps/accounts`**: Handles custom user models, authentication, and role-based access (Admin, Manager, Employee).
- **`apps/employees`**: Manages employee profiles, departments, and shifts.
- **`apps/attendance`**: Core logic for check-in/out records and attendance rules.
- **`apps/reports`**: Generates attendance summaries and payroll-ready reports.

---

## Modules & Features

### Accounts & Security
- **Role-Based Access Control (RBAC):** Users are assigned roles (Admin, Manager, Employee) that restrict access to specific features.
- **Face Recognition:** Supports capturing face encodings for biometrically verified attendance.

### Employee Management
- **Departments:** Organize staff into teams with designated heads.
- **Employee Profiles:** Detailed records including position, hire date, and status.
- **Shift Scheduling:** Flexible shift definitions (start/end times, grace periods, and breaks).

### Attendance Tracking
- **Check-in/Out:** Interface for employees to log their daily work.
- **Validation Rules:** Configurable rules for late arrivals and early departures.
- **Status Tracking:** Automatically marks attendance as Present, Late, Absent, or Half Day based on rules.

### Reporting
- **History View:** View individual or group attendance logs.
- **Data Export:** Export reports for payroll processing.

---

## Administrator Guide
Administrators can access the Django Admin interface at `/admin` to:
- Manage system-wide users and roles.
- Configure `AttendanceRule` settings.
- Directly edit database records if necessary.
- View system logs and manage global settings in `config.yaml`.

---

## User Guide
### For Employees:
- **Dashboard:** View current attendance status and notifications.
- **Check-in:** Use the Check-in page (requires login). If enabled, the system will use the camera for face verification.
- **Profile:** Manage personal information.

### For Managers:
- **Team Overview:** View attendance logs for employees in their department.
- **Reports:** Generate and download department-specific attendance reports.

---

## Troubleshooting
- **Database Errors:** Ensure `python manage.py migrate` was run. Check `db.sqlite3` permissions.
- **Face Detection Failures:** Ensure the webcam is accessible and lighting is adequate. Check if `face-recognition` and `opencv-python` are correctly installed.
- **Missing CSS/JS:** Run `python manage.py collectstatic` if deploying to production.
- **Dependency Issues:** Verify Python version is 3.10 and all `requirements.txt` packages are installed.

---
*Manual Version: 1.0 (April 2026)*

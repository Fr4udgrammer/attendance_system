<div align="center">

NOTE: This is still under development!!!

<img src="metadata/banner.png" alt="AttendanceX Banner" width="100%">

# 🕒 AttendanceX
### Modern Employee Attendance & Management System

[![GitHub License](https://img.shields.io/github/license/Fr4udgrammer/attendance_system?style=for-the-badge&color=00d1ff)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10-00d1ff?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-5.x-00d1ff?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Repo Size](https://img.shields.io/github/repo-size/Fr4udgrammer/attendance_system?style=for-the-badge&color=00d1ff)](https://github.com/Fr4udgrammer/attendance_system)

[**Explore Docs**](SYSTEM_MANUAL.md) • [**Report Bug**](https://github.com/Fr4udgrammer/attendance_system/issues) • [**Request Feature**](https://github.com/Fr4udgrammer/attendance_system/issues)

</div>

---

## 📖 Table of Contents
- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [🗺️ Roadmap](#️-roadmap)

---

## ✨ Key Features

<details open>
<summary><b>📊 Dynamic Dashboard</b></summary>
<br>
Get real-time insights into employee attendance, late arrivals, and absence rates with our modern dark-themed dashboard.
<br><br>
<img src="image.png" alt="Dashboard Overview" width="100%">
</details>

<details>
<summary><b>👤 Face Recognition Support</b></summary>
<br>
Seamless check-in/out experience with optional face profile verification for enhanced security.
<br><br>
<img src="image-1.png" alt="Face Recognition" width="100%">
</details>

<details>
<summary><b>📋 Comprehensive Reporting</b></summary>
<br>
- Detailed attendance history and summaries.
- Exportable data for administrative purposes.
- Department-wise analytics.
</details>

<details>
<summary><b>📱 Responsive UI</b></summary>
<br>
Fully optimized for mobile, tablet, and desktop with a collapsible sidebar and intuitive navigation.
</details>

---

## 🛠️ Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

</div>

---

## 🚀 Quick Start

<details>
<summary><b>1. Installation (Windows/Linux/macOS)</b></summary>

### Prerequisites
- Python 3.10+
- pip
- git

### Setup Steps
```bash
# Clone the repository
git clone https://github.com/Fr4udgrammer/attendance_system.git
cd attendance_system

# Create virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Migrate Database
python manage.py migrate
```
</details>

<details>
<summary><b>2. Running the Application</b></summary>

```bash
# Create admin access
python manage.py createsuperuser

# Start development server
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to start monitoring.
</details>

<details>
<summary><b>3. Docker Implementation</b></summary>

```bash
docker-compose up --build
```
</details>

---

## 📁 Project Structure

```bash
attendance_system/
├── apps/               # core applications (accounts, employees, attendance, reports)
├── media/              # uploaded employee face profiles
├── static/             # global CSS, JS, and Images
├── templates/          # global HTML templates
├── manage.py           # django management script
└── requirements.txt    # python dependencies
```

---

## 🗺️ Roadmap

- [x] Base Attendance System
- [x] Modern Dark Mode Dashboard
- [x] Mobile Responsive Layout
- [/] Advanced Face Liveness Detection
- [ ] Email Notifications for Late Arrivals
- [ ] Multi-tenant Support for Multiple Companies

---

<div align="center">
Made with ❤️ by Ryan Gwapo🤣
</div>

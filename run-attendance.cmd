@echo off
setlocal

cd /d "%~dp0"

if not exist ".\.venv310\Scripts\python.exe" (
  echo Error: .venv310 Python environment not found.
  echo Create it first or update this script path.
  pause
  exit /b 1
)

echo Running migrations...
".\.venv310\Scripts\python.exe" manage.py migrate --run-syncdb

echo Seeding initial data...
".\.venv310\Scripts\python.exe" manage.py setup_initial_data

echo.
echo Starting Django server at http://127.0.0.1:8000/
".\.venv310\Scripts\python.exe" manage.py runserver

endlocal

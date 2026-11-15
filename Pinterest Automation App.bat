@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "gui_app.py"
    exit /b
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" "gui_app.py"
    exit /b
)

pyw "gui_app.py"


@echo off

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist "%PROJECT_DIR%venv\Scripts\python.exe" (
    echo Project virtual environment not found. Run the setup steps in README.md first.
    exit /b 1
)

"%PROJECT_DIR%venv\Scripts\python.exe" -m main >> "%PROJECT_DIR%stock_log.txt" 2>&1

@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_PYTHON=%ROOT_DIR%\.venv311\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo ERROR: Python virtual environment not found at "%VENV_PYTHON%".
    echo Run setup_forge_env.cmd first.
    exit /b 1
)

"%VENV_PYTHON%" -m uvicorn forge.api.app:app --host 127.0.0.1 --port 8000

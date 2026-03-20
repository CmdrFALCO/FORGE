@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_PYTHON=%ROOT_DIR%\.venv311\Scripts\python.exe"
set "APP_PATH=%ROOT_DIR%forge\gui\app.py"

if not exist "%VENV_PYTHON%" (
    echo ERROR: Python virtual environment not found at "%VENV_PYTHON%".
    echo Create it first or re-run the FORGE environment setup.
    exit /b 1
)

if not exist "%APP_PATH%" (
    echo ERROR: Streamlit app not found at "%APP_PATH%".
    exit /b 1
)

"%VENV_PYTHON%" -m streamlit run "%APP_PATH%"


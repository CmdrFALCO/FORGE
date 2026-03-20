@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PY311=C:\Users\CmdrFALCO\AppData\Local\Programs\Python\Python311\python.exe"
set "VENV_DIR=%ROOT_DIR%\.venv311"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%PY311%" (
    echo ERROR: Python 3.11 was not found at "%PY311%".
    echo Install Python 3.11 first, then re-run this script.
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo Creating virtual environment at "%VENV_DIR%"...
    "%PY311%" -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

echo Upgrading pip tooling...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

echo Installing FORGE with GUI and CAD extras...
pushd "%ROOT_DIR%"
"%VENV_PYTHON%" -m pip install --no-build-isolation -e ".[gui,cad]"
set "INSTALL_EXIT=%ERRORLEVEL%"
popd

if not "%INSTALL_EXIT%"=="0" exit /b %INSTALL_EXIT%

echo.
echo Environment ready.
echo Start the app with: start_forge_app.cmd
echo Start the API with: start_forge_api.cmd

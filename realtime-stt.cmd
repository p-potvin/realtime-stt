@echo off
setlocal enabledelayedexpansion

:: VaultWares Project Launcher
:: Runs Real-Time STT in a dedicated virtual environment with CUDA support

set VENV_DIR=%~dp0.venv
set APP_MAIN=%~dp0main_app.py

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate"

echo Verifying dependencies...
pip install -r "%~dp0requirements.txt" --quiet

echo Starting Real-Time STT...
python "%APP_MAIN%" %*

pause

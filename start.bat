@echo off
echo ====================================
echo   Personal ChatBot - Quick Start
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Start the application
echo ====================================
echo   Starting Personal ChatBot...
echo   Open http://localhost:5000 in your browser
echo ====================================
echo.
python app.py

pause

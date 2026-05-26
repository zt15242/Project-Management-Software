@echo off
echo Starting Project Management System Backend...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Create uploads directory
if not exist "uploads\" (
    mkdir uploads
)

REM Run the application
echo Starting server at http://localhost:8000
echo API docs available at http://localhost:8000/docs
echo.
python main.py

pause


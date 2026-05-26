@echo off
echo Starting Project Management System Frontend...
echo.

REM Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies...
    npm install
    echo.
)

REM Run the application
echo Starting development server at http://localhost:3000
echo.
npm run dev

pause


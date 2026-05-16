@echo off
echo Setting up Anu Dashboard to start automatically on login using Task Scheduler...

:: Get the current directory where Anu is installed
set "anu_dir=%~dp0"
set "anu_dir=%anu_dir:~0,-1%"

:: Get the current username
for /f "tokens=*" %%a in ('whoami') do set current_user=%%a

:: Create the task in Task Scheduler
schtasks /create /tn "Anu Dashboard" /tr "pythonw.exe \"%anu_dir%\anu_dashboard.py\"" /sc onlogon /ru "%current_user%" /rl highest /f

if %errorlevel% equ 0 (
    echo Task created successfully!
    echo Anu Dashboard will now start automatically when you log in.
) else (
    echo Failed to create the task. Please run this script as administrator.
)

echo.
pause
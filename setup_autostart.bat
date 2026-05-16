@echo off
echo Setting up Anu Dashboard to start automatically on login...

:: Get the current directory where Anu is installed
set "anu_dir=%~dp0"
set "anu_dir=%anu_dir:~0,-1%"

:: Create a shortcut in the Windows Startup folder
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\AnuDashboard.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "pythonw.exe" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Arguments = "%anu_dir%\anu_dashboard.py" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%anu_dir%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Anu Dashboard" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "pythonw.exe,0" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo Anu Dashboard has been set to start automatically when you log in.
echo.
pause
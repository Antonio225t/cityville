@echo off

title CityVille Player Console

echo Starting the server...
start /min cmd /c "cd game && run_server.bat"
timeout 2 > nul

:start_browser
echo Starting the browser...
powershell -command "Start-Process .\chromium-82-0-4050\chrome-win\chrome.exe -ArgumentList "http://127.0.0.1:5000/" -Wait"
taskkill /f /fi "windowtitle eq CityVille Server" > nul 2>&1
taskkill /f /fi "windowtitle eq CityVille Server" > nul 2>&1
taskkill /f /fi "windowtitle eq Administrator:  CityVille Server" > nul 2>&1
taskkill /f /fi "windowtitle eq Administrator:  CityVille Server" > nul 2>&1
REM taskkill /f /im flask.exe > nul 2>&1
REM if %errorlevel% EQU 0 exit
REM taskkill /f /im python.exe > nul 2>&1
REM if %errorlevel% EQU 0 exit
REM taskkill /f /im cmd.exe > nul 2>&1
exit
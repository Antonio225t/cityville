@echo off

title CityVille Player Console
echo Checking Flash...
if exist C:\Windows\System32\Macromed\Flash\FlashUtil64_32_0_0_371_pepper.dll goto checking_python
echo Flash not installed. Installing Flash...
set HAS_INSTALLED=1
cd setup
powershell -command "Start-Process .\flashplayer32_0r0_371_winpep.exe -ArgumentList "-install" -Wait"
cd ..

:checking_python
echo Checking Python...
python --version > nul 2>&1
if %errorlevel% EQU 0 goto check_has_installed
cd setup
echo Python not installed. Installing Python (this might take 3 to 5 minutes)...
python-3.13.7-amd64.exe PrependPath=1 /quiet
set HAS_INSTALLED=1


:check_has_installed
if not defined HAS_INSTALLED goto check_python_requirements
echo.
echo Done installing. Please double click the "play.bat" file again for restarting the game.
pause
exit

:check_python_requirements
echo Checking python requirements
python -c "import flask" > nul 2>&1
if %errorlevel% GTR 0 goto install_requirements
python -c "import pyamf" > nul 2>&1
if %errorlevel% GTR 0 goto install_requirements
python -c "import xmltodict" > nul 2>&1
if %errorlevel% GTR 0 goto install_requirements
goto start_server

:install_requirements
echo Installing requirements...
cd setup
python -m pip install -r .\requirements.txt > nul
cd ..

:start_server
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
@echo off
title OF-Scraper Output Watcher ^& Organizer
color 0b

echo =====================================================================
echo            OF-Scraper Output Watcher ^& Folder Organizer
echo            Target Directory: F:\OF OUTPUT
echo =====================================================================
echo.
echo  [1] Start Live Watch Mode (monitors downloads and organizes live)
echo  [2] Run Once (instant single cleanup)
echo  [3] Exit
echo.
choice /c 123 /t 4 /d 1 /m "Select option (defaults to Watch Mode in 4s): "
if errorlevel 3 exit /b
if errorlevel 2 goto run_once
if errorlevel 1 goto watch_mode

:watch_mode
cls
py -3.12 "%~dp0organizer_watcher.py"
echo.
echo Watcher stopped.
pause
exit /b

:run_once
cls
py -3.12 "%~dp0organizer_watcher.py" --once
echo.
pause
exit /b

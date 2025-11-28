@echo off
echo Cleaning up previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

echo Building Flux Recorder with Icon and Metadata...
pyinstaller --noconsole --onefile --clean --icon=icon.ico --name="FluxRecorder" --version-file="version_info.txt" --add-data "icon.png;." --add-data "icon.ico;." --add-data "LICENSE;." recorder.py

echo.
echo Build complete! 
echo Note: If you still see the old icon, it might be the Windows Icon Cache. 
echo Try moving the .exe to a different folder to see the new icon.
pause

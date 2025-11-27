@echo off
echo ========================================
echo   Flux Screen Recorder - Installation
echo ========================================
echo.
echo Installing dependencies...
echo.

pip install -r requirements.txt

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To run the recorder:
echo   - Double-click run.bat
echo   - Or run: python recorder.py
echo.
echo To build standalone executable:
echo   - Run: build.bat
echo.
pause

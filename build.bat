@echo off
echo Building Flux Screen Recorder...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Build the executable
pyinstaller --name="FluxRecorder" ^
    --onefile ^
    --windowed ^
    --add-data "README.md;." ^
    recorder.py

echo.
echo Build complete! Executable is in the 'dist' folder.
pause

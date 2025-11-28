@echo off
echo Building Flux Screen Recorder...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Build the executable with icon
pyinstaller --name="FluxRecorder" ^
    --onefile ^
    --windowed ^
    --icon="icon.ico" ^
    --add-data "icon.png;." ^
    --add-data "icon.ico;." ^
    --add-data "README.md;." ^
    recorder_modern.py

echo.
echo Build complete! Executable is in the 'dist' folder.
pause

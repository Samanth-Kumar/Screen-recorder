@echo off
echo Building Uninstaller...
pyinstaller --noconsole --onefile --name="Uninstall" ..\app\uninstaller.py

echo Building Main Application...
pyinstaller --noconsole --onefile --clean --icon=..\assets\icon.ico --name="FluxRecorder" --version-file="..\assets\version_info.txt" --add-data "..\assets\icon.png;." --add-data "..\assets\icon.ico;." --add-data "..\LICENSE;." ..\app\recorder.py

echo Building Setup Wizard...
REM We need to bundle the EXEs we just built into the Setup EXE
REM Note: PyInstaller puts built EXEs in dist/ relative to where it runs.
REM Since we are running from scripts/, and we want to keep build artifacts there or in root?
REM By default pyinstaller creates dist/ in current dir.

pyinstaller --noconsole --onefile --name="FluxRecorderSetup" --icon=..\assets\icon.ico --add-data "dist\FluxRecorder.exe;." --add-data "dist\Uninstall.exe;." --add-data "..\LICENSE;." ..\app\setup.py

echo.
echo Build Complete!
echo The installer is located at: scripts\dist\FluxRecorderSetup.exe
pause

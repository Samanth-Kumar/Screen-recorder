@echo off
REM Change directory to the project root
cd /d "%~dp0.."

echo Building Uninstaller...
pyinstaller --noconsole --onefile --distpath scripts\dist --workpath scripts\build --specpath scripts --name="Uninstall" app\uninstaller.py

echo Building Main Application...
pyinstaller --noconsole --onefile --clean --distpath scripts\dist --workpath scripts\build --specpath scripts --icon="%CD%\assets\icon.ico" --name="FluxRecorder" --version-file="assets\version_info.txt" --add-data "%CD%\assets\icon.png;." --add-data "%CD%\assets\icon.ico;." --add-data "%CD%\LICENSE;." app\recorder.py

echo Building Setup Wizard...
pyinstaller --noconsole --onefile --distpath scripts\dist --workpath scripts\build --specpath scripts --name="FluxRecorder_Installer" --icon="%CD%\assets\icon.ico" --add-data "%CD%\scripts\dist\FluxRecorder.exe;." --add-data "%CD%\scripts\dist\Uninstall.exe;." --add-data "%CD%\LICENSE;." app\setup.py

echo.
echo Build Complete!
echo The installer is located at: scripts\dist\FluxRecorder_Installer.exe
pause

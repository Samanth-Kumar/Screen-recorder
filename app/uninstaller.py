import sys
import os
import shutil
import winshell
from win32com.client import Dispatch
from PyQt5.QtWidgets import QApplication, QMessageBox

def get_recordings_dir():
    return os.path.join(os.path.expanduser("~"), "Videos", "FluxRecordings")

def uninstall():
    app = QApplication(sys.argv)
    
    # 1. Ask to remove recordings
    rec_dir = get_recordings_dir()
    remove_data = False
    if os.path.exists(rec_dir):
        reply = QMessageBox.question(None, "Uninstall Flux Recorder", 
            f"Do you want to delete all recordings and data?\nLocation: {rec_dir}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            remove_data = True

    # 2. Confirm Uninstall
    confirm = QMessageBox.question(None, "Uninstall Flux Recorder",
        "Are you sure you want to uninstall Flux Recorder?",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    
    if confirm != QMessageBox.Yes:
        sys.exit()

    # 3. Perform Cleanup
    try:
        # Remove recordings if requested
        if remove_data and os.path.exists(rec_dir):
            try:
                shutil.rmtree(rec_dir)
            except Exception as e:
                QMessageBox.warning(None, "Error", f"Could not delete recordings: {e}")

        # Remove Shortcuts
        desktop = winshell.desktop()
        start_menu = winshell.programs()
        
        shortcut_name = "Flux Recorder.lnk"
        desktop_shortcut = os.path.join(desktop, shortcut_name)
        start_menu_shortcut = os.path.join(start_menu, "Samanth", shortcut_name)
        
        if os.path.exists(desktop_shortcut):
            os.remove(desktop_shortcut)
        
        if os.path.exists(start_menu_shortcut):
            os.remove(start_menu_shortcut)
            # Try to remove empty folder
            try:
                os.rmdir(os.path.dirname(start_menu_shortcut))
            except:
                pass

        # 4. Self-Destruct Sequence
        # We cannot delete the running executable directly.
        # We create a batch file to do it after this process ends.
        
        install_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        cleanup_bat = os.path.join(os.environ["TEMP"], "flux_cleanup.bat")
        
        with open(cleanup_bat, "w") as f:
            f.write("@echo off\n")
            f.write("timeout /t 2 /nobreak > NUL\n") # Wait for python to exit
            f.write(f'rmdir /s /q "{install_dir}"\n') # Try to delete the whole install folder
            f.write("del \"%~f0\"\n") # Delete this batch file
            
        # Launch batch file hidden
        os.startfile(cleanup_bat)
        
        QMessageBox.information(None, "Uninstalled", "Flux Recorder has been successfully removed.")
        sys.exit()
        
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Uninstall failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    uninstall()

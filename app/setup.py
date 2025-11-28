import sys
import os
import shutil
import winshell
import pythoncom
from win32com.client import Dispatch
from PyQt5.QtWidgets import QApplication, QMessageBox, QWizard, QWizardPage, QLabel, QVBoxLayout, QProgressBar, QLineEdit, QPushButton, QHBoxLayout, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

class InstallThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, install_dir):
        super().__init__()
        self.install_dir = install_dir
        
    def run(self):
        try:
            pythoncom.CoInitialize()
            # Create directory
            self.progress.emit(10)
            if not os.path.exists(self.install_dir):
                os.makedirs(self.install_dir)
            
            # Resource path helper
            def resource_path(relative_path):
                if hasattr(sys, '_MEIPASS'):
                    return os.path.join(sys._MEIPASS, relative_path)
                return os.path.join(os.path.abspath("."), relative_path)

            # Copy files
            files = ["FluxRecorder.exe", "Uninstall.exe", "LICENSE"]
            total_files = len(files)
            
            for i, filename in enumerate(files):
                src = resource_path(filename)
                dst = os.path.join(self.install_dir, filename)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                self.progress.emit(10 + int((i + 1) / total_files * 60))
            
            # Create Shortcuts
            self.progress.emit(80)
            self.create_shortcuts()
            
            self.progress.emit(100)
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            pythoncom.CoUninitialize()

    def create_shortcuts(self):
        target = os.path.join(self.install_dir, "FluxRecorder.exe")
        icon = target # Use exe icon
        
        # Desktop
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Flux Recorder.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = self.install_dir
        shortcut.IconLocation = icon
        shortcut.save()
        
        # Start Menu
        start_menu = winshell.programs()
        folder = os.path.join(start_menu, "Samanth")
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        path = os.path.join(folder, "Flux Recorder.lnk")
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = self.install_dir
        shortcut.IconLocation = icon
        shortcut.save()
        
        # Uninstall shortcut
        uninstall_target = os.path.join(self.install_dir, "Uninstall.exe")
        path = os.path.join(folder, "Uninstall Flux Recorder.lnk")
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = uninstall_target
        shortcut.WorkingDirectory = self.install_dir
        shortcut.IconLocation = uninstall_target
        shortcut.save()

class InstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flux Recorder Setup")
        self.setFixedSize(500, 400)
        
        # Default Install Dir
        self.default_dir = os.path.join(os.environ['LOCALAPPDATA'], 'FluxRecorder')
        
        self.addPage(self.create_intro_page())
        self.dir_page_id = self.addPage(self.create_directory_page())
        self.install_page_id = self.addPage(self.create_install_page())
        self.addPage(self.create_finish_page())
        
    def create_directory_page(self):
        page = QWizardPage()
        page.setTitle("Select Installation Folder")
        page.setSubTitle("Where do you want to install Flux Recorder?")
        
        layout = QVBoxLayout()
        
        h_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(self.default_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        
        h_layout.addWidget(self.dir_edit)
        h_layout.addWidget(browse_btn)
        
        layout.addLayout(h_layout)
        page.setLayout(layout)
        return page

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Install Folder", self.dir_edit.text())
        if directory:
            self.dir_edit.setText(directory)
        
    def create_intro_page(self):
        page = QWizardPage()
        page.setTitle("Welcome to Flux Recorder Setup")
        
        layout = QVBoxLayout()
        label = QLabel("This wizard will guide you through the installation of Flux Recorder.\n\n"
                      "It is recommended that you close all other applications before starting Setup.")
        label.setWordWrap(True)
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def create_install_page(self):
        page = QWizardPage()
        page.setTitle("Installing")
        
        layout = QVBoxLayout()
        self.status_label = QLabel("Ready to install...")
        layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        
        page.setLayout(layout)
        return page

    def create_finish_page(self):
        page = QWizardPage()
        page.setTitle("Installation Complete")
        
        layout = QVBoxLayout()
        label = QLabel("Flux Recorder has been installed on your computer.\n\n"
                      "Click Finish to close Setup.")
        label.setWordWrap(True)
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def initializePage(self, id):
        if id == self.install_page_id: # Install Page
            # Disable Back button
            self.button(QWizard.BackButton).setEnabled(False)
            self.button(QWizard.NextButton).setEnabled(False)
            
            # Start Install
            install_dir = self.dir_edit.text()
            self.thread = InstallThread(install_dir)
            self.thread.progress.connect(self.progress.setValue)
            self.thread.finished.connect(self.on_install_finished)
            self.thread.error.connect(self.on_install_error)
            self.thread.start()

    def on_install_finished(self):
        self.status_label.setText("Installation Complete!")
        self.button(QWizard.NextButton).setEnabled(True)
        self.button(QWizard.NextButton).click() # Auto advance

    def on_install_error(self, msg):
        QMessageBox.critical(self, "Installation Failed", f"Error: {msg}")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec_())

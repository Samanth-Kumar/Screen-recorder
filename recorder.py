import sys
import cv2
import numpy as np
import mss
import threading
import time
import keyboard
import win32gui
import win32con
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QFileDialog, QListWidget, QGroupBox, QMessageBox,
                             QStyle, QFrame, QRadioButton, QButtonGroup, QDialog,
                             QListWidgetItem, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QPen
import os


class RegionSelector(QWidget):
    """Overlay for selecting custom recording region"""
    region_selected = pyqtSignal(tuple)
    selection_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # Make it a top-level window
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Make window semi-transparent
        self.setWindowOpacity(0.5)
        
        self.start_pos = None
        self.end_pos = None
        self.selecting = False
        
        # Set cursor
        self.setCursor(Qt.CrossCursor)
        
        # Create instruction label
        self.instruction_label = QLabel(
            "🎯 Click and drag to select recording area | Press ESC to cancel", 
            self
        )
        self.instruction_label.setStyleSheet("""
            background-color: #4A9EFF;
            color: white;
            padding: 20px;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
        """)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.adjustSize()
        
        # Center the label
        label_x = (screen.width() - self.instruction_label.width()) // 2
        self.instruction_label.move(label_x, 30)
        
        # Size display label
        self.size_label = QLabel("", self)
        self.size_label.setStyleSheet("""
            background-color: #4A9EFF;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        self.size_label.hide()
        
    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.selecting = True
        self.size_label.show()
        self.update()
        
    def mouseMoveEvent(self, event):
        if self.selecting and self.start_pos:
            self.end_pos = event.pos()
            
            # Update size label
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = self.end_pos.x(), self.end_pos.y()
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            self.size_label.setText(f"📐 {w} × {h} pixels")
            self.size_label.adjustSize()
            
            # Position label near cursor
            label_x = min(x1, x2) + w // 2 - self.size_label.width() // 2
            label_y = max(y1, y2) + 20
            self.size_label.move(label_x, label_y)
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        if self.selecting and self.start_pos and self.end_pos:
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = self.end_pos.x(), self.end_pos.y()
            
            # Ensure x1,y1 is top-left
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            if width > 50 and height > 50:
                # Close this window first, then emit signal
                region_data = (x, y, width, height)
                self.close()
                # Use QTimer to emit after window is closed
                QTimer.singleShot(100, lambda: self.region_selected.emit(region_data))
            else:
                QMessageBox.warning(self, "Region Too Small", 
                                  "Please select a larger region (minimum 50×50 pixels)")
                self.selecting = False
                self.start_pos = None
                self.end_pos = None
                self.size_label.hide()
                self.update()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.selection_cancelled.emit()
            self.close()
    
    def closeEvent(self, event):
        # Emit cancelled if closing without selection
        if not self.start_pos or not self.end_pos:
            self.selection_cancelled.emit()
        event.accept()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw semi-transparent dark background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # Draw selection rectangle if selecting
        if self.selecting and self.start_pos and self.end_pos:
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = self.end_pos.x(), self.end_pos.y()
            
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            # Draw bright blue border
            pen = QPen(QColor(74, 158, 255), 4, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x, y, w, h)
            
            # Draw corner markers
            marker_size = 20
            painter.setBrush(QColor(74, 158, 255))
            
            # Top-left
            painter.drawRect(x - 2, y - 2, marker_size, 4)
            painter.drawRect(x - 2, y - 2, 4, marker_size)
            
            # Top-right
            painter.drawRect(x + w - marker_size + 2, y - 2, marker_size, 4)
            painter.drawRect(x + w - 2, y - 2, 4, marker_size)
            
            # Bottom-left
            painter.drawRect(x - 2, y + h - 2, marker_size, 4)
            painter.drawRect(x - 2, y + h - marker_size + 2, 4, marker_size)
            
            # Bottom-right
            painter.drawRect(x + w - marker_size + 2, y + h - 2, marker_size, 4)
            painter.drawRect(x + w - 2, y + h - marker_size + 2, 4, marker_size)


class WindowSelectorDialog(QDialog):
    """Dialog for selecting a window to record"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Window to Record")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.selected_window = None
        
        layout = QVBoxLayout()
        
        # Instructions
        label = QLabel("Select a window to record:")
        label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(label)
        
        # Window list
        self.window_list = QListWidget()
        self.window_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: 2px solid #4A9EFF;
                border-radius: 5px;
                padding: 5px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:hover {
                background-color: #2A2A2A;
            }
            QListWidget::item:selected {
                background-color: #4A9EFF;
            }
        """)
        self.window_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.window_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.populate_windows)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Populate windows
        self.populate_windows()
    
    def populate_windows(self):
        self.window_list.clear()
        
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((hwnd, title))
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        for hwnd, title in windows:
            item = QListWidgetItem(f"{title}")
            item.setData(Qt.UserRole, hwnd)
            self.window_list.addItem(item)
    
    def accept(self):
        current = self.window_list.currentItem()
        if current:
            self.selected_window = current.data(Qt.UserRole)
        super().accept()


class RecorderThread(QThread):
    """Thread for handling video recording"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, filename, fps, codec, quality, mode="monitor", monitor_number=1, window_hwnd=None, region=None):
        super().__init__()
        self.filename = filename
        self.fps = fps
        self.codec = codec
        self.quality = quality
        self.mode = mode
        self.monitor_number = monitor_number
        self.window_hwnd = window_hwnd
        self.region = region
        self.is_recording = False
        self.is_paused = False
        
    def run(self):
        try:
            sct = mss.mss()
            
            # Determine capture area
            if self.mode == "monitor":
                monitor = sct.monitors[self.monitor_number]
            elif self.mode == "window" and self.window_hwnd:
                rect = win32gui.GetWindowRect(self.window_hwnd)
                monitor = {
                    "left": rect[0],
                    "top": rect[1],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1]
                }
            elif self.mode == "region" and self.region:
                monitor = {
                    "left": self.region[0],
                    "top": self.region[1],
                    "width": self.region[2],
                    "height": self.region[3]
                }
            else:
                monitor = sct.monitors[1]
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            out = cv2.VideoWriter(
                self.filename,
                fourcc,
                self.fps,
                (monitor['width'], monitor['height'])
            )
            
            self.is_recording = True
            frame_interval = 1.0 / self.fps
            last_frame_time = time.time()
            
            while self.is_recording:
                if not self.is_paused:
                    current_time = time.time()
                    
                    # Only capture if enough time has passed
                    if current_time - last_frame_time >= frame_interval:
                        # Capture screen
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        
                        # Convert BGRA to BGR
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        
                        # Write frame
                        out.write(frame)
                        
                        last_frame_time = current_time
                    else:
                        # Sleep for a short time to avoid busy waiting
                        time.sleep(0.001)
                else:
                    time.sleep(0.1)
            
            out.release()
            sct.close()
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_recording = False


class ScreenRecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recorder_thread = None
        self.is_recording = False
        self.is_paused = False
        self.recording_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # Recording mode
        self.recording_mode = "monitor"
        self.selected_window = None
        self.selected_region = None
        
        # Default save location
        self.save_location = os.path.join(os.path.expanduser("~"), "Videos", "FluxRecordings")
        os.makedirs(self.save_location, exist_ok=True)
        
        # Minimize on record
        self.minimize_on_record = True
        
        self.init_ui()
        self.setup_hotkeys()
        
    def init_ui(self):
        self.setWindowTitle("Flux Screen Recorder")
        self.setGeometry(100, 100, 850, 700)
        
        # Set modern dark theme
        self.set_dark_theme()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🎥 Flux Screen Recorder")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4A9EFF; margin: 10px;")
        main_layout.addWidget(title)
        
        # Hotkey info
        hotkey_label = QLabel("⌨️ Hotkeys: Ctrl+Shift+R (Record/Stop) | Ctrl+Shift+P (Pause/Resume)")
        hotkey_label.setFont(QFont("Segoe UI", 9))
        hotkey_label.setAlignment(Qt.AlignCenter)
        hotkey_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        main_layout.addWidget(hotkey_label)
        
        # Recording Mode Group
        mode_group = QGroupBox("Recording Mode")
        mode_group.setStyleSheet(self.get_groupbox_style())
        mode_layout = QVBoxLayout()
        
        self.mode_button_group = QButtonGroup()
        
        self.monitor_radio = QRadioButton("Full Monitor")
        self.monitor_radio.setChecked(True)
        self.monitor_radio.toggled.connect(lambda: self.set_mode("monitor"))
        
        self.window_radio = QRadioButton("Specific Window")
        self.window_radio.toggled.connect(lambda: self.set_mode("window"))
        
        self.region_radio = QRadioButton("Custom Region")
        self.region_radio.toggled.connect(lambda: self.set_mode("region"))
        
        self.mode_button_group.addButton(self.monitor_radio)
        self.mode_button_group.addButton(self.window_radio)
        self.mode_button_group.addButton(self.region_radio)
        
        mode_layout.addWidget(self.monitor_radio)
        
        # Window selection button
        window_layout = QHBoxLayout()
        window_layout.addWidget(self.window_radio)
        self.select_window_btn = QPushButton("📌 Select Window")
        self.select_window_btn.setStyleSheet(self.get_button_style("#6C757D", 30))
        self.select_window_btn.clicked.connect(self.select_window)
        self.select_window_btn.setEnabled(False)
        window_layout.addWidget(self.select_window_btn)
        
        self.window_status_label = QLabel("(No window selected)")
        self.window_status_label.setStyleSheet("color: #888; font-size: 10px;")
        window_layout.addWidget(self.window_status_label)
        window_layout.addStretch()
        mode_layout.addLayout(window_layout)
        
        # Region selection button
        region_layout = QHBoxLayout()
        region_layout.addWidget(self.region_radio)
        self.select_region_btn = QPushButton("✂️ Select Region")
        self.select_region_btn.setStyleSheet(self.get_button_style("#6C757D", 30))
        self.select_region_btn.clicked.connect(self.select_region)
        self.select_region_btn.setEnabled(False)
        region_layout.addWidget(self.select_region_btn)
        
        self.region_status_label = QLabel("(No region selected)")
        self.region_status_label.setStyleSheet("color: #888; font-size: 10px;")
        region_layout.addWidget(self.region_status_label)
        region_layout.addStretch()
        mode_layout.addLayout(region_layout)
        
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)
        
        # Settings Group
        settings_group = QGroupBox("Recording Settings")
        settings_group.setStyleSheet(self.get_groupbox_style())
        settings_layout = QVBoxLayout()
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        quality_label.setFont(QFont("Segoe UI", 11))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["720p (30 FPS)", "1080p (30 FPS)", "1080p (60 FPS)", "4K (30 FPS)"])
        self.quality_combo.setCurrentIndex(1)
        self.quality_combo.setStyleSheet(self.get_combo_style())
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        settings_layout.addLayout(quality_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_label.setFont(QFont("Segoe UI", 11))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4 (H.264)", "AVI (XVID)", "MKV (H.264)"])
        self.format_combo.setStyleSheet(self.get_combo_style())
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        settings_layout.addLayout(format_layout)
        
        # Monitor selection (only for monitor mode)
        self.monitor_layout = QHBoxLayout()
        monitor_label = QLabel("Monitor:")
        monitor_label.setFont(QFont("Segoe UI", 11))
        self.monitor_combo = QComboBox()
        with mss.mss() as sct:
            for i in range(1, len(sct.monitors)):
                mon = sct.monitors[i]
                self.monitor_combo.addItem(f"Monitor {i} ({mon['width']}x{mon['height']})")
        self.monitor_combo.setStyleSheet(self.get_combo_style())
        self.monitor_layout.addWidget(monitor_label)
        self.monitor_layout.addWidget(self.monitor_combo)
        self.monitor_layout.addStretch()
        settings_layout.addLayout(self.monitor_layout)
        
        # Minimize checkbox
        self.minimize_checkbox = QCheckBox("Minimize window when recording starts")
        self.minimize_checkbox.setChecked(True)
        self.minimize_checkbox.toggled.connect(lambda checked: setattr(self, 'minimize_on_record', checked))
        settings_layout.addWidget(self.minimize_checkbox)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Timer display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Consolas", 32, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("""
            background-color: #1E1E1E;
            border: 2px solid #4A9EFF;
            border-radius: 10px;
            padding: 20px;
            color: #4A9EFF;
        """)
        main_layout.addWidget(self.timer_label)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.record_btn = QPushButton("⏺ Start Recording")
        self.record_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.record_btn.setMinimumHeight(50)
        self.record_btn.setStyleSheet(self.get_button_style("#28A745"))
        self.record_btn.clicked.connect(self.toggle_recording)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.pause_btn.setMinimumHeight(50)
        self.pause_btn.setStyleSheet(self.get_button_style("#FFC107"))
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        
        controls_layout.addWidget(self.record_btn)
        controls_layout.addWidget(self.pause_btn)
        main_layout.addLayout(controls_layout)
        
        # Recordings list
        recordings_group = QGroupBox("Recent Recordings")
        recordings_group.setStyleSheet(self.get_groupbox_style())
        recordings_layout = QVBoxLayout()
        
        self.recordings_list = QListWidget()
        self.recordings_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 5px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:hover {
                background-color: #2A2A2A;
            }
            QListWidget::item:selected {
                background-color: #4A9EFF;
            }
        """)
        self.recordings_list.itemDoubleClicked.connect(self.open_recording)
        recordings_layout.addWidget(self.recordings_list)
        
        # Buttons for recordings
        rec_buttons_layout = QHBoxLayout()
        
        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.setStyleSheet(self.get_button_style("#6C757D", 35))
        open_folder_btn.clicked.connect(self.open_recordings_folder)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(self.get_button_style("#6C757D", 35))
        refresh_btn.clicked.connect(self.refresh_recordings)
        
        rec_buttons_layout.addWidget(open_folder_btn)
        rec_buttons_layout.addWidget(refresh_btn)
        recordings_layout.addLayout(rec_buttons_layout)
        
        recordings_group.setLayout(recordings_layout)
        main_layout.addWidget(recordings_group)
        
        central_widget.setLayout(main_layout)
        
        # Load existing recordings
        self.refresh_recordings()
    
    def set_mode(self, mode):
        self.recording_mode = mode
        
        # Enable/disable relevant controls based on mode
        if mode == "window":
            self.select_window_btn.setEnabled(True)
            self.select_region_btn.setEnabled(False)
        elif mode == "region":
            self.select_window_btn.setEnabled(False)
            self.select_region_btn.setEnabled(True)
        else:  # monitor
            self.select_window_btn.setEnabled(False)
            self.select_region_btn.setEnabled(False)
        
        # Show/hide monitor selection
        for i in range(self.monitor_layout.count()):
            widget = self.monitor_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(mode == "monitor")
    
    def select_window(self):
        dialog = WindowSelectorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_window = dialog.selected_window
            if self.selected_window:
                title = win32gui.GetWindowText(self.selected_window)
                self.window_status_label.setText(f"✓ {title[:30]}...")
                self.window_status_label.setStyleSheet("color: #28A745; font-size: 10px;")
                QMessageBox.information(self, "Window Selected", f"Selected: {title}")
    
    def select_region(self):
        print("DEBUG: select_region called")  # Debug
        # Minimize the main window to get it out of the way
        self.showMinimized()
        
        # Small delay to ensure window is minimized before showing selector
        QTimer.singleShot(300, self._show_region_selector)
    
    def _show_region_selector(self):
        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self.on_region_selected)
        self.region_selector.selection_cancelled.connect(self.on_region_cancelled)
        print("DEBUG: Showing selector...")  # Debug
        self.region_selector.show()
        self.region_selector.raise_()
        self.region_selector.activateWindow()
        print("DEBUG: Selector shown")  # Debug
    
    def on_region_selected(self, region):
        # Restore the main window first
        self.showNormal()
        self.activateWindow()
        self.raise_()
        
        # Small delay to ensure window is fully restored
        QTimer.singleShot(150, lambda: self._show_confirmation_dialog(region))
    
    def _show_confirmation_dialog(self, region):
        # Ask for confirmation
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Region Selection")
        msg_box.setText(
            f"Selected region:\n\n"
            f"📐 Size: {region[2]} × {region[3]} pixels\n"
            f"📍 Position: ({region[0]}, {region[1]})\n\n"
            f"Is this the correct area to record?\n\n"
            f"Click 'Yes' to proceed or 'No' to select again."
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        msg_box.setIcon(QMessageBox.Question)
        
        # Ensure dialog is on top
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
        msg_box.activateWindow()
        msg_box.raise_()
        
        reply = msg_box.exec_()
        
        if reply == QMessageBox.Yes:
            # User confirmed - save the selection
            self.selected_region = region
            self.region_status_label.setText(f"✓ {region[2]}x{region[3]} at ({region[0]}, {region[1]})")
            self.region_status_label.setStyleSheet("color: #28A745; font-size: 10px;")
        else:
            # User clicked No - automatically retry selection
            self.selected_region = None
            self.region_status_label.setText("(No region selected)")
            self.region_status_label.setStyleSheet("color: #888; font-size: 10px;")
            
            # Automatically restart selection after a short delay
            QTimer.singleShot(200, self.select_region)
    
    def on_region_cancelled(self):
        # Restore the main window when selection is cancelled
        self.showNormal()
        self.activateWindow()
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            keyboard.add_hotkey('ctrl+shift+r', self.toggle_recording)
            keyboard.add_hotkey('ctrl+shift+p', self.toggle_pause)
        except:
            pass  # Hotkeys might fail if not running as admin
    
    def set_dark_theme(self):
        """Apply modern dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QGroupBox {
                color: #E0E0E0;
            }
            QRadioButton {
                color: #E0E0E0;
                font-size: 11px;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 11px;
            }
        """)
    
    def get_groupbox_style(self):
        return """
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #4A9EFF;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
    
    def get_combo_style(self):
        return """
            QComboBox {
                background-color: #1E1E1E;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 8px;
                min-width: 200px;
                font-size: 11px;
            }
            QComboBox:hover {
                border: 2px solid #4A9EFF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #E0E0E0;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E1E;
                border: 2px solid #4A9EFF;
                selection-background-color: #4A9EFF;
                color: #E0E0E0;
            }
        """
    
    def get_button_style(self, color, height=50):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #888;
            }}
        """
    
    def lighten_color(self, hex_color):
        """Lighten a hex color"""
        color = QColor(hex_color)
        return color.lighter(120).name()
    
    def darken_color(self, hex_color):
        """Darken a hex color"""
        color = QColor(hex_color)
        return color.darker(120).name()
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        # Validate mode-specific requirements
        if self.recording_mode == "window" and not self.selected_window:
            QMessageBox.warning(self, "No Window Selected", "Please select a window to record first.")
            return
        
        if self.recording_mode == "region" and not self.selected_region:
            QMessageBox.warning(self, "No Region Selected", "Please select a region to record first.")
            return
        
        # Get settings
        quality_text = self.quality_combo.currentText()
        format_text = self.format_combo.currentText()
        monitor_index = self.monitor_combo.currentIndex() + 1
        
        # Parse quality
        if "720p" in quality_text:
            fps = 30
        elif "1080p (60 FPS)" in quality_text:
            fps = 60
        elif "1080p" in quality_text:
            fps = 30
        elif "4K" in quality_text:
            fps = 30
        else:
            fps = 30
        
        # Parse format
        if "MP4" in format_text:
            codec = "mp4v"
            ext = ".mp4"
        elif "AVI" in format_text:
            codec = "XVID"
            ext = ".avi"
        elif "MKV" in format_text:
            codec = "X264"
            ext = ".mkv"
        else:
            codec = "mp4v"
            ext = ".mp4"
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mode_suffix = f"_{self.recording_mode}" if self.recording_mode != "monitor" else ""
        filename = os.path.join(self.save_location, f"recording_{timestamp}{mode_suffix}{ext}")
        
        # Start recording thread
        self.recorder_thread = RecorderThread(
            filename, fps, codec, quality_text,
            mode=self.recording_mode,
            monitor_number=monitor_index,
            window_hwnd=self.selected_window,
            region=self.selected_region
        )
        self.recorder_thread.finished.connect(self.on_recording_finished)
        self.recorder_thread.error.connect(self.on_recording_error)
        self.recorder_thread.start()
        
        # Update UI
        self.is_recording = True
        self.recording_time = 0
        self.timer.start(1000)
        self.record_btn.setText("⏹ Stop Recording")
        self.record_btn.setStyleSheet(self.get_button_style("#DC3545"))
        self.pause_btn.setEnabled(True)
        self.quality_combo.setEnabled(False)
        self.format_combo.setEnabled(False)
        self.monitor_combo.setEnabled(False)
        self.monitor_radio.setEnabled(False)
        self.window_radio.setEnabled(False)
        self.region_radio.setEnabled(False)
        
        # Minimize window if enabled
        if self.minimize_on_record:
            self.showMinimized()
    
    def stop_recording(self):
        if self.recorder_thread:
            self.recorder_thread.stop()
            self.recorder_thread.wait()
        
        # Restore window if minimized
        if self.isMinimized():
            self.showNormal()
            self.activateWindow()
        
        # Update UI
        self.is_recording = False
        self.is_paused = False
        self.timer.stop()
        self.record_btn.setText("⏺ Start Recording")
        self.record_btn.setStyleSheet(self.get_button_style("#28A745"))
        self.pause_btn.setText("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.quality_combo.setEnabled(True)
        self.format_combo.setEnabled(True)
        self.monitor_combo.setEnabled(True)
        self.monitor_radio.setEnabled(True)
        self.window_radio.setEnabled(True)
        self.region_radio.setEnabled(True)
    
    def toggle_pause(self):
        if not self.is_recording:
            return
            
        if not self.is_paused:
            self.recorder_thread.pause()
            self.is_paused = True
            self.pause_btn.setText("▶ Resume")
            self.pause_btn.setStyleSheet(self.get_button_style("#28A745"))
            self.timer.stop()
        else:
            self.recorder_thread.resume()
            self.is_paused = False
            self.pause_btn.setText("⏸ Pause")
            self.pause_btn.setStyleSheet(self.get_button_style("#FFC107"))
            self.timer.start(1000)
    
    def update_timer(self):
        self.recording_time += 1
        hours = self.recording_time // 3600
        minutes = (self.recording_time % 3600) // 60
        seconds = self.recording_time % 60
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def on_recording_finished(self):
        self.refresh_recordings()
        QMessageBox.information(self, "Success", "Recording saved successfully!")
    
    def on_recording_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Recording error: {error_msg}")
        self.stop_recording()
    
    def refresh_recordings(self):
        self.recordings_list.clear()
        if os.path.exists(self.save_location):
            files = [f for f in os.listdir(self.save_location) 
                    if f.endswith(('.mp4', '.avi', '.mkv'))]
            files.sort(reverse=True)
            for file in files:
                full_path = os.path.join(self.save_location, file)
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                self.recordings_list.addItem(f"{file} ({size_mb:.2f} MB)")
    
    def open_recording(self, item):
        filename = item.text().split(" (")[0]
        filepath = os.path.join(self.save_location, filename)
        os.startfile(filepath)
    
    def open_recordings_folder(self):
        os.startfile(self.save_location)
    
    def closeEvent(self, event):
        """Clean up hotkeys on close"""
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    window = ScreenRecorderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

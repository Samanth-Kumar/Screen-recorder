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
                             QListWidgetItem, QCheckBox, QKeySequenceEdit, QSlider, QTextEdit, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QPen, QPixmap, QKeySequence, QImage
import os
import pyaudio
import wave
import subprocess
import logging
import ctypes

# Setup logging
if getattr(sys, 'frozen', False):
    # In EXE mode, disable file logging or log only critical errors to console (which is hidden)
    logging.basicConfig(level=logging.CRITICAL)
else:
    # In development, log to file
    logging.basicConfig(filename='recorder_debug.log', level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

LICENSE_TEXT = """MIT License

Copyright (c) 2025 Samanth

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""



class HotkeySettingsDialog(QDialog):
    """Dialog for customizing hotkeys"""
    def __init__(self, parent=None, current_hotkeys=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkey Settings")
        self.setModal(True)
        self.setMinimumSize(400, 250)
        self.hotkeys = current_hotkeys or {
            "start_stop": "ctrl+shift+r",
            "pause_resume": "ctrl+shift+p"
        }
        self.recording_hotkey = None
        
        self.init_ui()
        self.set_dark_theme()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Instructions
        info = QLabel("Click on a box and press the desired key combination.")
        info.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info)
        
        # Start/Stop Hotkey
        h_layout1 = QHBoxLayout()
        label1 = QLabel("Start/Stop Recording:")
        label1.setFont(QFont("Segoe UI", 10))
        self.start_edit = QKeySequenceEdit(QKeySequence(self.hotkeys["start_stop"]))
        self.start_edit.setStyleSheet("background-color: #2A2A2A; color: white; padding: 5px; border-radius: 5px;")
        h_layout1.addWidget(label1)
        h_layout1.addWidget(self.start_edit)
        layout.addLayout(h_layout1)
        
        # Pause/Resume Hotkey
        h_layout2 = QHBoxLayout()
        label2 = QLabel("Pause/Resume Recording:")
        label2.setFont(QFont("Segoe UI", 10))
        self.pause_edit = QKeySequenceEdit(QKeySequence(self.hotkeys["pause_resume"]))
        self.pause_edit.setStyleSheet("background-color: #2A2A2A; color: white; padding: 5px; border-radius: 5px;")
        h_layout2.addWidget(label2)
        h_layout2.addWidget(self.pause_edit)
        layout.addLayout(h_layout2)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3B7EDD; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #5A6268; }
        """)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def get_hotkeys(self):
        return {
            "start_stop": self.start_edit.keySequence().toString().lower(),
            "pause_resume": self.pause_edit.keySequence().toString().lower()
        }

    def set_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #E0E0E0; }
            QLabel { color: #E0E0E0; }
        """)


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


class AudioRecorderThread(QThread):
    """Thread for handling audio recording"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.is_recording = False
        self.is_paused = False
        
    def run(self):
        try:
            # Audio settings
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 2
            RATE = 44100
            
            p = pyaudio.PyAudio()
            
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
            
            frames = []
            self.is_recording = True
            
            while self.is_recording:
                if not self.is_paused:
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(data)
                    except:
                        pass
                else:
                    time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save audio file
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_recording = False



class WebcamReader(threading.Thread):
    """Thread for reading webcam frames continuously"""
    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.running = True
        self.frame = None
        self.lock = threading.Lock()
        self.daemon = True  # Daemon thread ensures it dies with the app
        
    def run(self):
        try:
            cap = cv2.VideoCapture(self.camera_id)
            while self.running:
                ret, frame = cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                else:
                    time.sleep(0.1)
            cap.release()
        except Exception as e:
            logging.error(f"Webcam error: {e}")
            
    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
            
    def stop(self):
        self.running = False


class RecorderThread(QThread):
    """Thread for handling video recording"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, filename, fps, codec, quality, mode="monitor", monitor_number=1, window_hwnd=None, region=None, scale=1.0, record_webcam=False, webcam_id=0):
        super().__init__()
        self.filename = filename
        self.fps = fps
        self.codec = codec
        self.quality = quality
        self.mode = mode
        self.monitor_number = monitor_number
        self.window_hwnd = window_hwnd
        self.region = region
        self.scale = scale
        self.record_webcam = record_webcam
        self.webcam_id = webcam_id
        self.is_recording = False
        self.is_paused = False
        
    def run(self):
        webcam_reader = None
        try:
            # Start webcam if enabled
            if self.record_webcam:
                webcam_reader = WebcamReader(self.webcam_id)
                webcam_reader.start()
                time.sleep(0.5) # Warmup

            with mss.mss() as sct:
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
                
                # Calculate scaled dimensions
                scaled_width = int(monitor['width'] * self.scale)
                scaled_height = int(monitor['height'] * self.scale)
                
                # Setup video writer with scaled dimensions
                fourcc = cv2.VideoWriter_fourcc(*self.codec)
                out = cv2.VideoWriter(
                    self.filename,
                    fourcc,
                    self.fps,
                    (scaled_width, scaled_height)
                )
                
                if not out.isOpened():
                    raise Exception(f"Failed to open video writer with codec {self.codec}")
                
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
                            
                            # Scale frame if needed
                            if self.scale != 1.0:
                                frame = cv2.resize(frame, (scaled_width, scaled_height), interpolation=cv2.INTER_AREA)
                            
                            # Overlay webcam
                            if webcam_reader:
                                web_frame = webcam_reader.get_frame()
                                if web_frame is not None:
                                    try:
                                        # Resize webcam frame (1/5th of screen width)
                                        h, w, _ = frame.shape
                                        target_w = w // 5
                                        if target_w > 0:
                                            aspect_ratio = web_frame.shape[1] / web_frame.shape[0]
                                            target_h = int(target_w / aspect_ratio)
                                            
                                            web_frame_resized = cv2.resize(web_frame, (target_w, target_h))
                                            
                                            # Position: Bottom-Right with padding
                                            padding = 20
                                            y_offset = h - target_h - padding
                                            x_offset = w - target_w - padding
                                            
                                            # Ensure it fits
                                            if y_offset >= 0 and x_offset >= 0:
                                                frame[y_offset:y_offset+target_h, x_offset:x_offset+target_w] = web_frame_resized
                                    except Exception as e:
                                        # Ignore overlay errors to keep recording
                                        pass

                            # Write frame
                            out.write(frame)
                            
                            last_frame_time = current_time
                        else:
                            # Sleep for a short time to avoid busy waiting
                            time.sleep(0.001)
                    else:
                        time.sleep(0.1)
                
                out.release()
            
            if webcam_reader:
                webcam_reader.stop()
                webcam_reader.join()
            
            self.finished.emit()
            
        except Exception as e:
            if webcam_reader:
                webcam_reader.stop()
            self.error.emit(str(e))
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_recording = False




class VideoTrimmerDialog(QDialog):
    """Dialog for trimming videos"""
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trim Video")
        self.setModal(True)
        self.resize(600, 500)
        self.video_path = video_path
        
        # Open video
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        self.start_time = 0.0
        self.end_time = self.duration
        
        self.init_ui()
        self.set_dark_theme()
        
        # Show first frame
        self.update_preview(0)
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Preview Label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("background-color: black; border: 1px solid #444;")
        layout.addWidget(self.preview_label)
        
        # Sliders Layout
        sliders_layout = QVBoxLayout()
        
        # Time display
        self.time_label = QLabel(f"Time: 00:00 / {self.format_time(self.duration)}")
        self.time_label.setAlignment(Qt.AlignCenter)
        sliders_layout.addWidget(self.time_label)
        
        # Main Slider (Seek)
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, self.total_frames)
        self.seek_slider.valueChanged.connect(self.on_seek)
        sliders_layout.addWidget(self.seek_slider)
        
        # Controls Layout
        controls_layout = QHBoxLayout()
        
        # Start Time
        controls_layout.addWidget(QLabel("Start:"))
        self.start_label = QLabel("00:00")
        self.start_label.setStyleSheet("color: #4A9EFF; font-weight: bold;")
        controls_layout.addWidget(self.start_label)
        
        set_start_btn = QPushButton("[ Set Start")
        set_start_btn.clicked.connect(self.set_start_time)
        controls_layout.addWidget(set_start_btn)
        
        controls_layout.addStretch()
        
        # End Time
        controls_layout.addWidget(QLabel("End:"))
        self.end_label = QLabel(self.format_time(self.duration))
        self.end_label.setStyleSheet("color: #DC3545; font-weight: bold;")
        controls_layout.addWidget(self.end_label)
        
        set_end_btn = QPushButton("Set End ]")
        set_end_btn.clicked.connect(self.set_end_time)
        controls_layout.addWidget(set_end_btn)
        
        sliders_layout.addLayout(controls_layout)
        layout.addLayout(sliders_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        trim_btn = QPushButton("✂️Save")
        trim_btn.clicked.connect(self.trim_video)
        trim_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(trim_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
        
    def update_preview(self, frame_no):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self.cap.read()
        if ret:
            # Resize to fit label
            h, w, c = frame.shape
            target_h = 300
            scale = target_h / h
            target_w = int(w * scale)
            frame = cv2.resize(frame, (target_w, target_h))
            
            # Convert to QPixmap
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.preview_label.setPixmap(QPixmap.fromImage(qt_img))
            
            # Update time label
            current_sec = frame_no / self.fps if self.fps > 0 else 0
            self.time_label.setText(f"Time: {self.format_time(current_sec)} / {self.format_time(self.duration)}")
            
    def on_seek(self, value):
        self.update_preview(value)
        
    def set_start_time(self):
        frame = self.seek_slider.value()
        self.start_time = frame / self.fps
        self.start_label.setText(self.format_time(self.start_time))
        
    def set_end_time(self):
        frame = self.seek_slider.value()
        self.end_time = frame / self.fps
        self.end_label.setText(self.format_time(self.end_time))
        
    def trim_video(self):
        if self.start_time >= self.end_time:
            QMessageBox.warning(self, "Invalid Range", "Start time must be before end time.")
            return
            
        # Use ffmpeg to trim
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        base, ext = os.path.splitext(self.video_path)
        output_path = f"{base}_trimmed{ext}"
        
        cmd = [
            ffmpeg_exe, '-i', self.video_path,
            '-ss', str(self.start_time),
            '-to', str(self.end_time),
            '-c', 'copy', # Fast stream copy
            '-y',
            output_path
        ]
        
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            subprocess.run(cmd, check=True, startupinfo=startupinfo)
            QMessageBox.information(self, "Success", f"Trimmed video saved as:\n{os.path.basename(output_path)}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to trim video:\n{e}")

    def set_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #E0E0E0; }
            QLabel { color: #E0E0E0; }
            QSlider::groove:horizontal {
                border: 1px solid #333;
                height: 8px;
                background: #2A2A2A;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4A9EFF;
                border: 1px solid #4A9EFF;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
        """)


class LicenseDialog(QDialog):
    """Dialog for displaying the license"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License")
        self.setMinimumSize(600, 450)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Flux Screen Recorder License")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #4A9EFF; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # License Text
        text_edit = QTextEdit()
        text_edit.setPlainText(LICENSE_TEXT)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(text_edit)
        
        # Close Button
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3B7EDD; }
        """)
        
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.set_dark_theme()
        
    def set_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #121212; color: #E0E0E0; }
            QLabel { color: #E0E0E0; }
        """)


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
        
        # Default hotkeys
        self.hotkeys = {
            "start_stop": "ctrl+shift+r",
            "pause_resume": "ctrl+shift+p"
        }
        
        self.init_ui()
        self.setup_hotkeys()
        
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
            return os.path.join(base_path, relative_path)
        except Exception:
            # In dev, assets are in ../assets relative to this file
            base_path = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(base_path)
            asset_path = os.path.join(project_root, "assets", relative_path)
            return asset_path

    def init_ui(self):
        self.setWindowTitle("Flux Screen Recorder")
        self.setGeometry(100, 100, 850, 700)
        
        # Set window icon
        icon_path = self.resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Set modern dark theme
        self.set_dark_theme()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # Reduced spacing
        main_layout.setContentsMargins(15, 15, 15, 15)  # Reduced margins
        

        
        # Header with Icon and License
        header_layout = QHBoxLayout()
        
        # Left spacer
        header_layout.addStretch()
        
        # Center content (Icon + Title)
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0,0,0,0)
        
        # Icon
        icon_label = QLabel()
        icon_pixmap = QPixmap(self.resource_path("icon.png"))
        if not icon_pixmap.isNull():
            scaled_pixmap = icon_pixmap.scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        center_layout.addWidget(icon_label)
        
        # Title
        title = QLabel("Flux Screen Recorder")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))  # Reduced font
        title.setStyleSheet("color: #4A9EFF; margin: 5px;")
        center_layout.addWidget(title)
        
        header_layout.addWidget(center_container)
        
        # Right spacer
        header_layout.addStretch()
        
        # License Button
        license_btn = QPushButton("📜")
        license_btn.setToolTip("View License")
        license_btn.setFixedSize(30, 30)
        license_btn.clicked.connect(self.show_license)
        license_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #333;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #4A9EFF;
                border-color: #4A9EFF;
                background-color: #1E1E1E;
            }
        """)
        header_layout.addWidget(license_btn)
        
        # Settings Button
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("Configure Hotkeys")
        settings_btn.setFixedSize(30, 30)
        settings_btn.clicked.connect(self.open_hotkey_settings)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #333;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #4A9EFF;
                border-color: #4A9EFF;
                background-color: #1E1E1E;
            }
        """)
        header_layout.addWidget(settings_btn)
        
        main_layout.addLayout(header_layout)
        
        
        # Recording Mode Group
        mode_group = QGroupBox("Recording Mode")
        mode_group.setStyleSheet(self.get_groupbox_style())
        mode_layout = QVBoxLayout()
        mode_layout.setContentsMargins(10, 10, 10, 10) # Reduced margins
        
        # Modern segmented button control
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Full Monitor Button
        self.monitor_btn = QPushButton("🖥️ Full Monitor")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.setChecked(True)
        self.monitor_btn.setMinimumHeight(40) # Reduced height
        self.monitor_btn.clicked.connect(lambda: self.set_mode("monitor"))
        buttons_layout.addWidget(self.monitor_btn)
        
        # Specific Window Button
        self.window_btn = QPushButton("🪟 Specific Window")
        self.window_btn.setCheckable(True)
        self.window_btn.setMinimumHeight(40) # Reduced height
        self.window_btn.clicked.connect(lambda: self.set_mode("window"))
        buttons_layout.addWidget(self.window_btn)
        
        # Custom Region Button
        self.region_btn = QPushButton("✂️ Custom Region")
        self.region_btn.setCheckable(True)
        self.region_btn.setMinimumHeight(40) # Reduced height
        self.region_btn.clicked.connect(lambda: self.set_mode("region"))
        buttons_layout.addWidget(self.region_btn)
        
        # Apply modern button style
        mode_button_style = """
            QPushButton {
                background-color: #2A2A2A;
                border: 2px solid #4A4A4A;
                border-radius: 8px;
                color: #E0E0E0;
                font-size: 11px;
                font-weight: 500;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #4A9EFF;
            }
            QPushButton:checked {
                background-color: #4A9EFF;
                border-color: #4A9EFF;
                color: white;
                font-weight: bold;
            }
        """
        self.monitor_btn.setStyleSheet(mode_button_style)
        self.window_btn.setStyleSheet(mode_button_style)
        self.region_btn.setStyleSheet(mode_button_style)
        
        mode_layout.addLayout(buttons_layout)
        
        # Status/Action area
        self.mode_status_widget = QWidget()
        self.mode_status_layout = QVBoxLayout(self.mode_status_widget)
        self.mode_status_layout.setContentsMargins(0, 5, 0, 0)
        self.mode_status_layout.setSpacing(5)
        
        # Window selection controls (hidden by default)
        self.window_controls = QWidget()
        window_controls_layout = QHBoxLayout(self.window_controls)
        window_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_window_btn = QPushButton("📌 Select Window")
        self.select_window_btn.setStyleSheet(self.get_button_style("#6C757D", 30))
        self.select_window_btn.clicked.connect(self.select_window)
        window_controls_layout.addWidget(self.select_window_btn)
        
        self.window_status_label = QLabel("(No window selected)")
        self.window_status_label.setStyleSheet("color: #888; font-size: 10px;")
        window_controls_layout.addWidget(self.window_status_label)
        window_controls_layout.addStretch()
        self.window_controls.hide()
        
        # Region selection controls (hidden by default)
        self.region_controls = QWidget()
        region_controls_layout = QHBoxLayout(self.region_controls)
        region_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.select_region_btn = QPushButton("✂️ Select Region")
        self.select_region_btn.setStyleSheet(self.get_button_style("#6C757D", 30))
        self.select_region_btn.clicked.connect(self.select_region)
        region_controls_layout.addWidget(self.select_region_btn)
        
        self.region_status_label = QLabel("(No region selected)")
        self.region_status_label.setStyleSheet("color: #888; font-size: 10px;")
        region_controls_layout.addWidget(self.region_status_label)
        region_controls_layout.addStretch()
        self.region_controls.hide()
        
        self.mode_status_layout.addWidget(self.window_controls)
        self.mode_status_layout.addWidget(self.region_controls)
        mode_layout.addWidget(self.mode_status_widget)
        
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)
        
        # Settings Group
        settings_group = QGroupBox("Recording Settings")
        settings_group.setStyleSheet(self.get_groupbox_style())
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(10, 15, 10, 10)
        settings_layout.setSpacing(10)
        
        # Grid for dropdowns
        from PyQt5.QtWidgets import QGridLayout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Quality
        quality_label = QLabel("Quality:")
        quality_label.setFont(QFont("Segoe UI", 10))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["360p (30 FPS)", "720p (30 FPS)", "1080p (30 FPS)", "1080p (60 FPS)", "4K (30 FPS)"])
        self.quality_combo.setCurrentIndex(2)  # Default to 1080p (30 FPS)
        self.quality_combo.setStyleSheet(self.get_combo_style())
        grid_layout.addWidget(quality_label, 0, 0)
        grid_layout.addWidget(self.quality_combo, 0, 1)
        
        # Format
        format_label = QLabel("Format:")
        format_label.setFont(QFont("Segoe UI", 10))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4 (H.264)", "AVI (XVID)", "MKV (H.264)"])
        self.format_combo.setStyleSheet(self.get_combo_style())
        grid_layout.addWidget(format_label, 1, 0)
        grid_layout.addWidget(self.format_combo, 1, 1)
        
        # Monitor (only for monitor mode)
        self.monitor_label = QLabel("Monitor:")
        self.monitor_label.setFont(QFont("Segoe UI", 10))
        self.monitor_combo = QComboBox()
        with mss.mss() as sct:
            for i in range(1, len(sct.monitors)):
                mon = sct.monitors[i]
                self.monitor_combo.addItem(f"Monitor {i} ({mon['width']}x{mon['height']})")
        self.monitor_combo.setStyleSheet(self.get_combo_style())
        grid_layout.addWidget(self.monitor_label, 2, 0)
        grid_layout.addWidget(self.monitor_combo, 2, 1)
        
        # Save Location
        save_loc_label = QLabel("Save to:")
        save_loc_label.setFont(QFont("Segoe UI", 10))
        
        save_loc_layout = QHBoxLayout()
        self.save_loc_input = QLineEdit(self.save_location)
        self.save_loc_input.setReadOnly(True)
        self.save_loc_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 5px;
                color: #888;
                font-size: 11px;
            }
        """)
        
        browse_btn = QPushButton("📂")
        browse_btn.setToolTip("Change Save Location")
        browse_btn.setFixedSize(30, 30)
        browse_btn.clicked.connect(self.change_save_location)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A2A2A;
                border: 2px solid #333;
                border-radius: 5px;
                color: #E0E0E0;
            }
            QPushButton:hover {
                border-color: #4A9EFF;
                background-color: #333;
            }
        """)
        
        save_loc_layout.addWidget(self.save_loc_input)
        save_loc_layout.addWidget(browse_btn)
        
        grid_layout.addWidget(save_loc_label, 3, 0)
        grid_layout.addLayout(save_loc_layout, 3, 1)
        
        settings_layout.addLayout(grid_layout)
        
        # Minimize checkbox
        self.minimize_checkbox = QCheckBox("🔽 Minimize window when recording starts")
        self.minimize_checkbox.setChecked(True)
        self.minimize_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E0E0E0;
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #666;
                border-radius: 4px;
                background: #2A2A2A;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #4A9EFF;
            }
            QCheckBox::indicator:checked {
                background: #4A9EFF;
                border-color: #4A9EFF;
            }
            QCheckBox:checked {
                color: #4A9EFF;
            }
        """)
        self.minimize_checkbox.toggled.connect(lambda checked: setattr(self, 'minimize_on_record', checked))
        settings_layout.addWidget(self.minimize_checkbox)
        
        # Microphone checkbox
        self.microphone_checkbox = QCheckBox("🎤 Record Microphone Audio")
        self.microphone_checkbox.setChecked(False)
        self.microphone_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E0E0E0;
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #666;
                border-radius: 4px;
                background: #2A2A2A;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #4A9EFF;
            }
            QCheckBox::indicator:checked {
                background: #4A9EFF;
                border-color: #4A9EFF;
            }
            QCheckBox:checked {
                color: #4A9EFF;
            }
        """)
        self.record_audio = False
        self.microphone_checkbox.toggled.connect(self.toggle_microphone)
        settings_layout.addWidget(self.microphone_checkbox)
        
        # Webcam checkbox
        self.webcam_checkbox = QCheckBox("📷 Record Webcam")
        self.webcam_checkbox.setChecked(False)
        self.webcam_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E0E0E0;
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #666;
                border-radius: 4px;
                background: #2A2A2A;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #4A9EFF;
            }
            QCheckBox::indicator:checked {
                background: #4A9EFF;
                border-color: #4A9EFF;
            }
            QCheckBox:checked {
                color: #4A9EFF;
            }
        """)
        self.record_webcam = False
        self.webcam_checkbox.toggled.connect(lambda checked: setattr(self, 'record_webcam', checked))
        settings_layout.addWidget(self.webcam_checkbox)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Timer display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Consolas", 28, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("""
            background-color: #1E1E1E;
            border: 2px solid #4A9EFF;
            border-radius: 10px;
            padding: 10px;
            color: #4A9EFF;
        """)
        main_layout.addWidget(self.timer_label)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.record_btn = QPushButton("⏺ Start Recording")
        self.record_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.record_btn.setMinimumHeight(40)
        self.record_btn.setStyleSheet(self.get_button_style("#28A745"))
        self.record_btn.clicked.connect(self.toggle_recording)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.pause_btn.setMinimumHeight(40)
        self.pause_btn.setStyleSheet(self.get_button_style("#FFC107"))
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        
        controls_layout.addWidget(self.record_btn)
        controls_layout.addWidget(self.pause_btn)
        main_layout.addLayout(controls_layout)
        
        # Recent Recordings Group (Restored)
        recordings_group = QGroupBox("Recent Recordings")
        recordings_group.setStyleSheet(self.get_groupbox_style())
        recordings_layout = QVBoxLayout()
        recordings_layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll area for recordings
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                background-color: #2A2A2A;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #4A9EFF;
                border-radius: 5px;
            }
        """)
        
        self.recordings_container = QWidget()
        self.recordings_layout = QVBoxLayout(self.recordings_container)
        self.recordings_layout.setSpacing(2) # Reduced spacing
        self.recordings_layout.setContentsMargins(2, 2, 2, 2)
        self.recordings_layout.addStretch()
        
        scroll_area.setWidget(self.recordings_container)
        recordings_layout.addWidget(scroll_area)
        
        # Buttons for recordings
        rec_buttons_layout = QHBoxLayout()
        
        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.setMinimumHeight(25)
        open_folder_btn.setStyleSheet(self.get_button_style("#6C757D", 25))
        open_folder_btn.clicked.connect(self.open_recordings_folder)
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.setMinimumHeight(25)
        refresh_btn.setStyleSheet(self.get_button_style("#4A9EFF", 25))
        refresh_btn.clicked.connect(self.refresh_recordings)
        
        rec_buttons_layout.addWidget(open_folder_btn)
        rec_buttons_layout.addWidget(refresh_btn)
        recordings_layout.addLayout(rec_buttons_layout)
        
        recordings_group.setLayout(recordings_layout)
        main_layout.addWidget(recordings_group)
        
        central_widget.setLayout(main_layout)
        
        # Initial refresh
        QTimer.singleShot(500, self.refresh_recordings)

    
    def set_mode(self, mode):
        self.recording_mode = mode
        
        # Update button states
        self.monitor_btn.setChecked(mode == "monitor")
        self.window_btn.setChecked(mode == "window")
        self.region_btn.setChecked(mode == "region")
        
        # Show/hide appropriate controls
        self.window_controls.setVisible(mode == "window")
        self.region_controls.setVisible(mode == "region")
        
        # Show/hide monitor selection
        self.monitor_label.setVisible(mode == "monitor")
        self.monitor_combo.setVisible(mode == "monitor")
        
        # Auto-trigger selection dialogs
        if mode == "window":
            QTimer.singleShot(100, self.select_window)
        elif mode == "region":
            QTimer.singleShot(100, self.select_region)
    
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
        # Minimize the main window to get it out of the way
        self.showMinimized()
        
        # Small delay to ensure window is minimized before showing selector
        QTimer.singleShot(300, self._show_region_selector)
    
    def _show_region_selector(self):
        self.region_selector = RegionSelector()
        self.region_selector.region_selected.connect(self.on_region_selected)
        self.region_selector.selection_cancelled.connect(self.on_region_cancelled)
        self.region_selector.show()
        self.region_selector.raise_()
        self.region_selector.activateWindow()
    
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
            keyboard.unhook_all_hotkeys()
            keyboard.add_hotkey(self.hotkeys["start_stop"], self.toggle_recording)
            keyboard.add_hotkey(self.hotkeys["pause_resume"], self.toggle_pause)
            

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
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #666;
                border-radius: 4px;
                background: #2A2A2A;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #4A9EFF;
            }
            QCheckBox::indicator:checked {
                background: #4A9EFF;
                border-color: #4A9EFF;
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
        
        # Parse quality and determine resolution scale
        if "360p" in quality_text:
            fps = 30
            scale = 0.5  # Scale down to 50% for smaller files
        elif "720p" in quality_text:
            fps = 30
            scale = 0.75  # Scale down to 75%
        elif "1080p (60 FPS)" in quality_text:
            fps = 60
            scale = 1.0  # Full resolution
        elif "1080p" in quality_text:
            fps = 30
            scale = 1.0  # Full resolution
        elif "4K" in quality_text:
            fps = 30
            scale = 1.0  # Full resolution
        else:
            fps = 30
            scale = 1.0
        
        # Parse format - use reliable codecs to prevent crashes
        if "MP4" in format_text:
            codec = "mp4v"  # MPEG-4 Part 2 - most reliable on Windows
            ext = ".mp4"
        elif "AVI" in format_text:
            codec = "XVID"  # XVID - very reliable
            ext = ".avi"
        elif "MKV" in format_text:
            codec = "XVID"  # XVID works well in MKV too
            ext = ".mkv"
        else:
            codec = "mp4v"
            ext = ".mp4"
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mode_suffix = f"_{self.recording_mode}" if self.recording_mode != "monitor" else ""
        filename = os.path.join(self.save_location, f"recording_{timestamp}{mode_suffix}{ext}")
        
        # Store filenames for potential audio merging
        self.video_filename = filename
        self.audio_filename = None
        self.audio_thread = None
        
        # Start video recording thread
        self.recorder_thread = RecorderThread(
            filename, fps, codec, quality_text,
            mode=self.recording_mode,
            monitor_number=monitor_index,
            window_hwnd=self.selected_window,
            region=self.selected_region,
            scale=scale,
            record_webcam=self.record_webcam,
            webcam_id=0
        )
        self.recorder_thread.finished.connect(self.on_recording_finished)
        self.recorder_thread.error.connect(self.on_recording_error)
        self.recorder_thread.start()
        
        # Start audio recording if enabled
        if self.record_audio:
            self.audio_filename = os.path.join(self.save_location, f"audio_{timestamp}.wav")
            self.audio_thread = AudioRecorderThread(self.audio_filename)
            self.audio_thread.error.connect(self.on_recording_error)
            self.audio_thread.start()
        
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
        self.monitor_btn.setEnabled(False)
        self.window_btn.setEnabled(False)
        self.region_btn.setEnabled(False)
        
        # Minimize window if enabled
    
        # Minimize window if enabled
        if self.minimize_on_record:
            self.showMinimized()
    
    def stop_recording(self):
        logging.info("Stop recording requested")
        try:
            if self.recorder_thread:
                logging.info("Stopping video thread...")
                self.recorder_thread.stop()
                if not self.recorder_thread.wait(2000):
                    logging.warning("Video thread did not stop in time")
                else:
                    logging.info("Video thread stopped")
            
            # Stop audio recording if it was running
            if self.audio_thread:
                logging.info("Stopping audio thread...")
                self.audio_thread.stop()
                if not self.audio_thread.wait(2000):
                    logging.warning("Audio thread did not stop in time")
                else:
                    logging.info("Audio thread stopped")
                
                # Merge audio and video if both exist
                if self.audio_filename and os.path.exists(self.audio_filename) and os.path.exists(self.video_filename):
                    logging.info("Merging audio and video...")
                    self.merge_audio_video()
            
            # Restore window if minimized
            if self.isMinimized():
                self.showNormal()
                self.activateWindow()
            
            # Update UI
            self.is_recording = False
            self.is_paused = False
            self.timer.stop()
            self.recording_time = 0
            self.timer_label.setText("00:00:00")
            self.record_btn.setText("⏺ Start Recording")
            self.record_btn.setStyleSheet(self.get_button_style("#28A745"))
            self.pause_btn.setText("⏸ Pause")
            self.pause_btn.setEnabled(False)
            self.quality_combo.setEnabled(True)
            self.format_combo.setEnabled(True)
            self.monitor_combo.setEnabled(True)
            self.monitor_btn.setEnabled(True)
            self.window_btn.setEnabled(True)
            self.region_btn.setEnabled(True)
            logging.info("Stop recording completed successfully")
            
        except Exception as e:
            logging.error(f"Error in stop_recording: {e}")
            QMessageBox.critical(self, "Error Stopping", f"An error occurred while stopping:\n{str(e)}")
            # Force reset UI state
            self.is_recording = False
            self.timer.stop()
            self.record_btn.setText("⏺ Start Recording")
            self.record_btn.setStyleSheet(self.get_button_style("#28A745"))
            self.pause_btn.setEnabled(False)
            self.quality_combo.setEnabled(True)
            self.format_combo.setEnabled(True)

    
    def merge_audio_video(self):
        """Merge audio and video files using ffmpeg"""
        ffmpeg_exe = None
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            import shutil
            if shutil.which("ffmpeg"):
                ffmpeg_exe = "ffmpeg"
        
        if not ffmpeg_exe:
            logging.warning("FFmpeg not found. Audio file saved separately.")
            QMessageBox.warning(self, "FFmpeg Missing", 
                "FFmpeg is not installed.\n"
                "Audio file saved separately.")
            return

        try:
            # Create output filename
            base_name = os.path.splitext(self.video_filename)[0]
            ext = os.path.splitext(self.video_filename)[1]
            output_filename = f"{base_name}_with_audio{ext}"
            
            # Use ffmpeg to merge
            cmd = [
                ffmpeg_exe, '-i', self.video_filename,
                '-i', self.audio_filename,
                '-c:v', 'copy',  # Copy video without re-encoding
                '-c:a', 'aac',   # Encode audio to AAC
                '-filter:a', 'volume=5.0', # Boost volume significantly (5x)
                '-strict', 'experimental',
                '-y',  # Overwrite output file
                output_filename
            ]
            
            # Hide console window for ffmpeg on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            
            if result.returncode == 0:
                # Success - delete original files and rename
                if os.path.exists(self.video_filename):
                    os.remove(self.video_filename)
                if os.path.exists(self.audio_filename):
                    os.remove(self.audio_filename)
                os.rename(output_filename, self.video_filename)
                logging.info("Audio merge successful")
            else:
                # FFmpeg failed - keep both files
                logging.error(f"FFmpeg failed: {result.stderr}")
                QMessageBox.warning(self, "Merge Failed", 
                    "Failed to merge audio and video.\n"
                    "Audio file has been saved separately.")
                    
        except Exception as e:
            logging.error(f"Audio merge failed: {e}")
            QMessageBox.warning(self, "Merge Error", 
                f"An error occurred while merging audio:\n{str(e)}\n\n"
                "Audio file has been saved separately.")
    
    def toggle_pause(self):
        if not self.is_recording:
            return
            
        if not self.is_paused:
            self.recorder_thread.pause()
            if self.audio_thread:
                self.audio_thread.pause()
            self.is_paused = True
            self.pause_btn.setText("▶ Resume")
            self.pause_btn.setStyleSheet(self.get_button_style("#28A745"))
            self.timer.stop()
        else:
            self.recorder_thread.resume()
            if self.audio_thread:
                self.audio_thread.resume()
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

    def show_license(self):
        """Show the license dialog"""
        dialog = LicenseDialog(self)
        dialog.exec_()
    
    def refresh_recordings(self):
        # Clear existing widgets
        while self.recordings_layout.count() > 1:  # Keep the stretch
            item = self.recordings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if os.path.exists(self.save_location):
            files = [f for f in os.listdir(self.save_location) 
                    if f.endswith(('.mp4', '.avi', '.mkv'))]
            files.sort(reverse=True)
            
            for file in files:
                full_path = os.path.join(self.save_location, file)
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                
                # Create recording item widget
                item_widget = QWidget()
                item_widget.setStyleSheet("""
                    QWidget {
                        background-color: #2A2A2A;
                        border-radius: 5px;
                        padding: 2px;
                    }
                    QWidget:hover {
                        background-color: #333;
                    }
                """)
                
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 2, 5, 2)
                item_layout.setSpacing(5)
                
                # File info
                info_label = QLabel(f"{file} ({size_mb:.2f} MB)")
                info_label.setStyleSheet("color: #E0E0E0; font-size: 11px;")
                item_layout.addWidget(info_label)
                item_layout.addStretch()
                
                # Play button
                play_btn = QPushButton("►")
                play_btn.setFixedSize(24, 24)
                play_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28A745;
                        border: none;
                        border-radius: 4px;
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
                play_btn.setToolTip("Play recording")
                play_btn.clicked.connect(lambda checked, f=full_path: self.play_recording(f))
                item_layout.addWidget(play_btn)
                
                # Trim button
                trim_btn = QPushButton("✂️")
                trim_btn.setFixedSize(24, 24)
                trim_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6C757D;
                        border: none;
                        border-radius: 4px;
                        color: white;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #5A6268;
                    }
                """)
                trim_btn.setToolTip("Trim recording")
                trim_btn.clicked.connect(lambda checked, f=full_path: self.trim_recording(f))
                item_layout.addWidget(trim_btn)
                
                # Delete button
                delete_btn = QPushButton("🗑")
                delete_btn.setFixedSize(24, 24)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #DC3545;
                        border: none;
                        border-radius: 4px;
                        color: white;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #C82333;
                    }
                """)
                delete_btn.setToolTip("Delete recording")
                delete_btn.clicked.connect(lambda checked, f=full_path, w=item_widget: self.delete_recording(f, w))
                item_layout.addWidget(delete_btn)
                
                # Add to layout (before stretch)
                self.recordings_layout.insertWidget(self.recordings_layout.count() - 1, item_widget)
    
    def play_recording(self, filepath):
        """Play a recording"""
        if os.path.exists(filepath):
            os.startfile(filepath)
            
    def trim_recording(self, filepath):
        """Open video trimmer dialog"""
        if os.path.exists(filepath):
            dialog = VideoTrimmerDialog(filepath, self)
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_recordings()
    
    def delete_recording(self, filepath, widget):
        """Delete a recording after confirmation"""
        filename = os.path.basename(filepath)
        
        reply = QMessageBox.question(
            self,
            "Delete Recording",
            f"Are you sure you want to delete this recording?\n\n{filename}\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(filepath)
                widget.deleteLater()
                QMessageBox.information(self, "Deleted", "Recording deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete recording:\n{str(e)}")
    
    def toggle_microphone(self, checked):
        if checked:
            try:
                import imageio_ffmpeg
                imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                QMessageBox.warning(self, "Dependency Missing", 
                    "The 'imageio-ffmpeg' library is required for audio merging.\n"
                    "Please install it using: pip install imageio-ffmpeg")
        self.record_audio = checked

    def open_hotkey_settings(self):
        """Open hotkey settings dialog"""
        dialog = HotkeySettingsDialog(self, self.hotkeys)
        if dialog.exec_() == QDialog.Accepted:
            self.hotkeys = dialog.get_hotkeys()
            self.setup_hotkeys()
            QMessageBox.information(self, "Hotkeys Updated", "Hotkeys have been updated successfully!")

    def change_save_location(self):
        """Change the folder where recordings are saved"""
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.save_location)
        if folder:
            self.save_location = folder
            self.save_loc_input.setText(folder)
            self.refresh_recordings() # Refresh list to show files in new folder (if any)

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
    # Set AppUserModelID to show custom icon in taskbar
    myappid = 'flux.screen.recorder.v1' # Arbitrary string
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    # Enforce executable name integrity
    if getattr(sys, 'frozen', False):
        executable_name = os.path.basename(sys.executable)
        if executable_name.lower() != "fluxrecorder.exe":
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Integrity Error", 
                "Application integrity check failed.\n\n"
                "The executable name has been modified.\n"
                "Please rename it back to 'FluxRecorder.exe' to run this application.")
            sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    window = ScreenRecorderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

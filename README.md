# 🎥 Flux Screen Recorder

A modern, feature-rich screen recorder built with Python and PyQt5.

## ✨ Features

### 📹 **Recording Modes**
- **Full Monitor** - Record entire screen
- **Specific Window** - Record a single application window
- **Custom Region** - Select any area of your screen with visual selector

### 🎙️ **Audio & Video**
- **Microphone Recording** - Record voiceover with your screen
- **Webcam Overlay** - Add a facecam to your recordings (bottom-right)
- **High Quality** - Support for 720p, 1080p (30/60 FPS), and 4K

### ✂️ **Editing Tools**
- **Video Trimming** - Built-in tool to trim your recordings
- **Instant Preview** - Play recordings directly within the app

### ⚙️ **Controls & Settings**
- **Global Hotkeys** - Customizable hotkeys for Start/Stop and Pause/Resume
- **Auto-Minimize** - Option to minimize app when recording starts
- **Taskbar Icon** - Fully integrated with Windows taskbar

## 📁 Project Structure

```
Screen recorder/
├── recorder.py          # Main application source code
├── requirements.txt     # Python dependencies
├── icon.ico            # Application icon
├── build.bat           # Script to build standalone executable
├── run.bat             # Script to run from source
├── README.md           # Documentation
└── .gitignore          # Git configuration
```

## 🚀 Quick Start

### Option 1: Run from Source

1. **Install Python 3.7+**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the recorder:**
```bash
python recorder.py
```

### Option 2: Build Standalone Executable

1. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. **Build the executable:**
```bash
pyinstaller --noconfirm --onefile --windowed --icon "icon.ico" --name "FluxRecorder" --add-data "icon.ico;." recorder.py
```
(Or use the provided `build.bat` if available)

## ⚠️ Installation Note (Windows SmartScreen)

When you run the `FluxRecorder.exe` for the first time, you might see a blue window saying **"Windows protected your PC"**.

This happens because the application is not digitally signed (which requires a paid certificate). **It is safe to run.**

To proceed:
1. Click **"More info"**.
2. Click **"Run anyway"**.

This will only happen once.


## 📖 Usage Guide

### 1. Select Recording Mode
- **Monitor**: Choose which screen to record.
- **Window**: Select a specific open window.
- **Region**: Drag to select a custom area.

### 2. Configure Settings
- **Quality**: Choose from 360p to 4K.
- **Microphone**: Toggle to record audio.
- **Webcam**: Toggle to show webcam overlay.
- **Hotkeys**: Click the "Hotkeys" text to customize shortcuts.

### 3. Record & Edit
- Press **Start** or use Hotkey (`Ctrl+Shift+R` by default).
- After recording, use the **Play (►)** button to watch.
- Use the **Scissors (✂️)** button to trim the video.

## 🔧 Requirements

- **OS**: Windows 10/11
- **Python**: 3.7+
- **Dependencies**:
  - `PyQt5` (UI)
  - `opencv-python` (Video processing)
  - `mss` (Screen capture)
  - `pyaudio` (Audio recording)
  - `imageio-ffmpeg` (Video/Audio merging & trimming)
  - `keyboard` (Global hotkeys)
  - `pywin32` (Window management)

## 🤝 Contributing

Contributions are welcome! We'd love to see your improvements.
1. **Fork** the project
2. Create your **Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. Open a **Pull Request**

## 📝 License

Distributed under the **MIT License**. See `LICENSE` file for more information.

---

**Built with 💙 by Samanth**

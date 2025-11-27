# 🎥 Flux Screen Recorder

A modern, feature-rich screen recorder built with Python and PyQt5.

## ✨ Features

### 📹 **Recording Modes**
- **Full Monitor** - Record entire screen
- **Specific Window** - Record a single application window
- **Custom Region** - Select any area of your screen with visual selector

### 🎬 **Recording Controls**
- ⏺ Start/Stop Recording
- ⏸ Pause/Resume
- ⏱ Real-time timer display
- Auto-minimize on recording start

### ⚙️ **Quality Options**
- 720p @ 30 FPS
- 1080p @ 30 FPS
- 1080p @ 60 FPS
- 4K @ 30 FPS

### 📦 **Format Support**
- MP4 (H.264)
- AVI (XVID)
- MKV (H.264)

### ⌨️ **Global Hotkeys**
- `Ctrl+Shift+R` - Start/Stop Recording
- `Ctrl+Shift+P` - Pause/Resume
- Works even when minimized!

### 🖥️ **Multi-Monitor Support**
- Record from any connected monitor
- Automatic monitor detection

### 🎨 **Modern UI**
- Dark theme
- Clean, intuitive interface
- Recent recordings list with file sizes
- Quick access to recordings folder
- Visual region selector with confirmation

## 📁 Project Structure

```
Screen recorder/
├── recorder.py          # Main application
├── requirements.txt     # Python dependencies
├── build.bat           # Build standalone executable
├── run.bat             # Run from source
├── README.md           # This file
├── FluxRecorder.spec   # PyInstaller configuration
└── dist/               # Built executables (after build)
    └── FluxRecorder.exe
```

## 🚀 Quick Start

### Option 1: Run from Source

1. **Install Python 3.7+** (if not already installed)

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the recorder:**
```bash
run.bat
```
Or directly:
```bash
python recorder.py
```

### Option 2: Build Standalone Executable

1. **Install dependencies** (if not done):
```bash
pip install -r requirements.txt
```

2. **Build the executable:**
```bash
build.bat
```

3. **Run the executable:**
   - Navigate to `dist` folder
   - Double-click `FluxRecorder.exe`
   - Or use `dist\FluxRecorder.exe`

## 📖 Usage Guide

### Recording Full Monitor
1. Select "Full Monitor" (default)
2. Choose monitor if you have multiple displays
3. Click "⏺ Start Recording"
4. Click "⏹ Stop Recording" when done

### Recording Specific Window
1. Select "Specific Window"
2. Click "📌 Select Window"
3. Choose the application window from the list
4. Click "⏺ Start Recording"

### Recording Custom Region
1. Select "Custom Region"
2. Click "✂️ Select Region"
3. Main window minimizes automatically
4. Click and drag to select the area
5. Confirm or retry the selection
6. Click "⏺ Start Recording"

### Using Hotkeys
- Press `Ctrl+Shift+R` to start/stop recording anytime
- Press `Ctrl+Shift+P` to pause/resume during recording
- Hotkeys work even when the app is minimized!

## 💾 Recordings Location

All recordings are automatically saved to:
```
C:\Users\<YourUsername>\Videos\FluxRecordings\
```

You can access this folder quickly using the "📁 Open Folder" button in the app.

## 🔧 Requirements

- **OS**: Windows 10/11
- **Python**: 3.7+ (for running from source)
- **Dependencies**: See `requirements.txt`
  - opencv-python
  - numpy
  - mss
  - pillow
  - PyQt5
  - keyboard
  - pywin32

## ⚠️ Troubleshooting

### Application won't start
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try running as administrator if hotkeys don't work

### Recording is laggy
- Try lowering the quality/FPS setting
- Close other resource-intensive applications
- Use a faster codec (try AVI instead of MP4)

### Can't find recordings
- Check: `C:\Users\<YourUsername>\Videos\FluxRecordings\`
- Use the "📁 Open Folder" button in the app
- Check the "Recent Recordings" list in the app

### Region selector not visible
- Make sure to click the "Custom Region" radio button first
- The main window will minimize when selector appears
- Look for a semi-transparent dark overlay on your screen

### Hotkeys not working
- Try running the application as administrator
- Make sure no other application is using the same hotkey combination
- Hotkeys: `Ctrl+Shift+R` and `Ctrl+Shift+P`

### Video plays too fast/slow
- This has been fixed in the latest version
- If you still experience issues, try a different quality setting

## 🎯 Tips & Tricks

1. **Best Quality**: Use 1080p @ 60 FPS for smooth recordings
2. **Smallest File Size**: Use 720p @ 30 FPS with AVI format
3. **Quick Recording**: Use hotkeys to start/stop without switching windows
4. **Region Recording**: Perfect for recording specific parts of applications
5. **Window Recording**: Automatically follows the window even if you move it

## 📝 License

Free to use, no watermarks, open source.

## 🙏 Credits

Built with:
- Python
- PyQt5 (UI Framework)
- OpenCV (Video Processing)
- MSS (Screen Capture)
- Keyboard (Global Hotkeys)

---

**Enjoy recording! 🎬**

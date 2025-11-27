# Flux Screen Recorder

A modern, feature-rich screen recorder built with Python and PyQt5.

## Features

✅ **Multiple Quality Options**
- 720p @ 30 FPS
- 1080p @ 30 FPS
- 1080p @ 60 FPS
- 4K @ 30 FPS

✅ **Multiple Format Support**
- MP4 (H.264)
- AVI (XVID)
- MKV (H.264)

✅ **Recording Controls**
- Start/Stop Recording
- Pause/Resume
- Real-time timer display

✅ **Multi-Monitor Support**
- Record from any connected monitor
- Automatic monitor detection

✅ **Modern UI**
- Dark theme
- Clean, intuitive interface
- Recent recordings list
- Quick access to recordings folder

## Installation

### Option 1: Run from Source

1. Install dependencies:
```bash
install.bat
```

2. Run the recorder:
```bash
run.bat
```

Or directly:
```bash
python recorder.py
```

### Option 2: Build Standalone Executable

1. Install dependencies first (if not done):
```bash
install.bat
```

2. Build the executable:
```bash
build.bat
```

3. Find the executable in the `dist` folder

## Usage

1. **Select Quality**: Choose your desired recording quality
2. **Select Format**: Choose output format (MP4, AVI, or MKV)
3. **Select Monitor**: Choose which monitor to record
4. **Start Recording**: Click "Start Recording" button
5. **Pause/Resume**: Use the pause button during recording
6. **Stop**: Click "Stop Recording" when done

Recordings are automatically saved to:
`C:\Users\<YourUsername>\Videos\FluxRecordings\`

## Requirements

- Python 3.7+
- Windows 10/11
- See `requirements.txt` for Python dependencies

## Troubleshooting

**Issue**: Application won't start
- Make sure all dependencies are installed: `pip install -r requirements.txt`

**Issue**: Recording is laggy
- Try lowering the quality/FPS setting
- Close other resource-intensive applications

**Issue**: Can't find recordings
- Check: `C:\Users\<YourUsername>\Videos\FluxRecordings\`
- Use the "Open Folder" button in the app

## License

Free to use, no watermarks, open source.

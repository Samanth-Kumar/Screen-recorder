@echo off
echo Starting Flux Recorder Web Server...
echo Please open your browser to: http://localhost:8000
cd src
python -m http.server 8000

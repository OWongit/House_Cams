# RTSP Fullscreen Viewer (OpenCV)

A tiny Python script that opens an RTSP/RTSPS video stream in a **fullscreen** window using OpenCV, automatically **retries** if the stream drops, and lets you **quit** with `q` or `Esc`.

## Camera View
![RTSP fullscreen window](images/cam_view.png)

## Features
- Prefers the **FFmpeg** backend (`cv2.CAP_FFMPEG`) when available for robust RTSP handling
- Fullscreen display via OpenCV highgui
- Automatic reconnect with a configurable delay (`RETRY_SECONDS`, default 60s)
- Graceful exit with `q` or `Esc`

## Requirements
- **Python** 3.9+
- **pip** (or uv/poetry if you prefer)
- OS GUI support for OpenCV windows (e.g., X11 on Linux, Quartz on macOS, Win32 on Windows)
- (Recommended) **FFmpeg** installed on your system for broader codec/RTSP support

## Install
```bash
# optional but recommended: create a virtual environment
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# install python deps
pip install -r requirements.txt

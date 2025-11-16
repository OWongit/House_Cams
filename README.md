# RTSP Fullscreen Viewer - Dual-Stream

A tiny Python script that opens one or TWO RTSP/RTSPS video streams in a single **fullscreen** window using OpenCV. 
Each stream reconnects automatically if it drops, and you can **quit** with `q` or `Esc`. 
The viewer uses a custom black canvas for letterboxing so there are no white gutters in fullscreen.

## Camera View
![RTSP side-by-side fullscreen](images/cam_view.png)

## What’s new
- **Two concurrent streams** shown **side-by-side** in one window.
- **Independent reconnect** per stream with the same `RETRY_SECONDS` backoff.
- **Background reader threads** for smooth playback while the UI stays responsive.
- **Black letterbox background** (our own canvas) so fullscreen margins aren’t white.
- **Status overlays** on each tile (e.g., `LIVE`, `FROZEN`, `connecting...`).

## Features
- Prefers the **FFmpeg** backend (`cv2.CAP_FFMPEG`) when available for robust RTSP handling.
- Fullscreen display via OpenCV HighGUI.
- Automatic reconnect with a configurable delay (`RETRY_SECONDS`, default 60s).
- Graceful exit with `q` or `Esc`.

## Requirements
- **Python** 3.9+
- **NumPy** (for the mosaic/canvas)
- **OpenCV** (e.g., `opencv-python`)
- OS GUI support for OpenCV windows (e.g., X11 on Linux, Quartz on macOS, Win32 on Windows)
- (Recommended) **FFmpeg** installed on your system for broader codec/RTSP support

## Install
```bash
# 1) from requirements.txt
pip install -r requirements.txt
# 2) or directly
pip install opencv-python numpy
```
 
## Configure
In the script, set:
- `rtsp_url_1` / `rtsp_url_2` - your two RTSP/RTSPS URLs
- `name_left` / `name_right` - overlay titles for each camera
- `RETRY_SECONDS` – reconnect delay (default 60s)
- `TARGET_HEIGHT` – per-tile height before mosaicking (bigger = larger tiles)


## Controls
- `q` or `Esc` – quit
- (Optional) To make the window resizable instead of fullscreen, remove the line that sets `WND_PROP_FULLSCREEN` in the script.

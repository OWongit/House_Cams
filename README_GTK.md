# UniFi Dual-Cam Viewer — GTK + GStreamer Edition

This refactor removes PyQt6/OpenCV and replaces the UI with **PyGObject (GTK 3)**
and video with **GStreamer (playbin + gtksink)**.

## What changed
- **PyQt6** UI ➜ **GTK 3** (`gi.repository.Gtk`)
- **OpenCV VideoCapture thread** ➜ **GStreamer playbin** with automatic demux/decoding
- Timestamp overlay now uses GStreamer's `timeoverlay` filter.
- Reconnect/backoff handled via GStreamer Bus messages.

## Run
1. Install Python deps:
   ```bash
   pip install -r requirements.txt
   ```
2. Install system GStreamer + plugins (varies by OS). See comments inside `requirements.txt`.
3. Provide `KEYS.py` next to the sources with values for:
   ```python
   keys = {
       "CONSOLE_IP": "1.2.3.4",
       "API_KEY": "your_api_key",
       "FRONT_CAMERA": "camera-id-1",
       "BACK_CAMERA": "camera-id-2",
   }
   ```
4. Run the app:
   ```bash
   python3 main.py
   ```

## Files
- `main.py` — GTK application wiring + stream URL discovery
- `ui_main.py` — GTK UI (two resizable panes, status labels)
- `streaming.py` — GStreamer controller (playbin + gtksink, timeoverlay, reconnect)
- `helper.py` — UniFi Protect helpers (unchanged)

## Notes
- If `gtksink` isn't available, the code falls back to `autovideosink` (embedding may be less seamless).
- For very low latency, consider installing the `-bad` plugins and tweaking RTSP-specific properties by replacing
  `playbin` with an explicit `rtspsrc ! ... ! gtksink` pipeline.

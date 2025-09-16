# UniFi Dual-Cam RTSP GUI (PyQt6)

A simple PyQt6 GUI that displays two UniFi Protect camera streams stacked vertically with a time overlay
in the top‑right corner of each stream. It uses the UniFi Protect Integration API to fetch RTSPS URLs,
converts them to plain RTSP, and then streams via OpenCV.

## Features
- Two camera views (front & back) shown vertically
- Time overlay on each stream (local time)
- Resilient reconnect (will attempt to reopen streams if connection drops)
- Clean shutdown

## Requirements
- Python 3.9+ recommended
- Accessible UniFi Protect Console on your LAN
- Valid API Key with UniFi Protect integration permissions
- The two camera IDs (as provided in your `KEYS.py`)

### Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration
Copy or edit `KEYS.py` with your values:

```python
# KEYS.py
keys = {
    "API_KEY": "YOUR_API_KEY_HERE",
    "CONSOLE_IP": "YOUR_CONSOLE_IP_HERE",
    "BACK_CAMERA": "YOUR_CAM_ID_HERE",
    "FRONT_CAMERA": "YOUR_CAM_ID_HERE"
}
```

## Run
```bash
python main.py
```

If the UI opens but you see "No Signal" for a while, the app is attempting to connect/reconnect.
Make sure your console IP and API key are correct and that the Protect integration is enabled
for the requested stream quality (default is `high`).

## Notes
- This app disables TLS verification for the local Protect HTTPS call (self-signed certs are common on LAN).
- The app converts **rtsps** (SRTP) to **rtsp** (TCP/UDP) using the standard UniFi port mapping (7441 -> 7447).
- OpenCV uses FFmpeg under the hood for RTSP. If you run into performance issues, try a wired connection for the host.


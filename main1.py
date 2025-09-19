import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from KEYS import keys
from helper import fetch_stream_url, rtsps_to_rtsp
from streaming1 import VideoStreamWorker
from ui_main1 import MainWindow

QUALITY = "high"  # 'high' | 'medium' | 'low'

def main():
    # DPI-friendly defaults:
    # Qt6 enables high-DPI scaling automatically, but keep robust across versions.
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    try:
        # Available in Qt 6.5+: avoid blurry scaling on Windows multi-monitor
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)

    front_id = keys.get("FRONT_CAMERA")
    back_id  = keys.get("BACK_CAMERA")

    if not front_id or not back_id:
        raise SystemExit("FRONT_CAMERA and BACK_CAMERA must be set in KEYS.py")

    # Fetch RTSPS -> convert to RTSP
    try:
        front_rtsps = fetch_stream_url(front_id, quality=QUALITY)
        back_rtsps  = fetch_stream_url(back_id,  quality=QUALITY)

        front_rtsp = rtsps_to_rtsp(front_rtsps)
        back_rtsp  = rtsps_to_rtsp(back_rtsps)
    except Exception as e:
        print("Failed to fetch/convert camera URLs:", e)
        print("The UI will still open, but streams won't show until this is resolved.")
        front_rtsp = ""
        back_rtsp  = ""

    win = MainWindow()
    win.show()

    # start workers
    front_worker = VideoStreamWorker(front_rtsp, name="Front")
    back_worker  = VideoStreamWorker(back_rtsp,  name="Back")

    win.bind_streams(front_worker, back_worker)

    # Only start if URL is non-empty
    if front_rtsp:
        front_worker.start()
    if back_rtsp:
        back_worker.start()

    # Ensure threads stop on close
    def on_close():
        front_worker.stop()
        back_worker.stop()

    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

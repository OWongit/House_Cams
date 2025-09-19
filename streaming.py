import threading
import time
import datetime
import cv2
import numpy as np
from PIL import Image

class VideoStreamWorker(threading.Thread):
    """OpenCV-based RTSP reader with reconnect/backoff and timestamp overlay.
    Emits frames via a callable 'on_frame' (PIL.Image) and status via 'on_status' (str).
    Safe for use with Tkinter when UI updates are scheduled back onto the main thread.
    """

    def __init__(self, rtsp_url: str, name: str = "Camera", on_frame=None, on_status=None):
        super().__init__(daemon=True)
        self.rtsp_url = rtsp_url
        self.name = name
        self.on_frame = on_frame
        self.on_status = on_status
        self._stopping = False
        self._cap = None
        self._last_status = ""

    # ---- helpers ----
    def _emit_status(self, msg: str):
        if msg != self._last_status:
            self._last_status = msg
            if callable(self.on_status):
                try:
                    self.on_status(msg)
                except Exception:
                    pass

    def _open(self):
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
        self._cap = cv2.VideoCapture(self.rtsp_url)
        # Reduce buffering for lower latency, best-effort
        try:
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

    def _overlay_timestamp(self, frame_bgr):
        """Draw a semi-transparent bg box + white timestamp at top-right."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        h, w = frame_bgr.shape[:2]

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1

        (text_w, text_h), baseline = cv2.getTextSize(now_str, font, font_scale, thickness)
        margin = 10

        x2 = w - margin
        y1 = margin
        x1 = x2 - text_w - 2 * margin
        y2 = y1 + text_h + baseline + margin

        # ensure bounds
        x1 = max(0, x1)
        y1 = max(0, y1)

        # overlay box
        overlay = frame_bgr.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
        # blend for semi-transparency
        alpha = 0.5
        cv2.addWeighted(overlay, alpha, frame_bgr, 1 - alpha, 0, frame_bgr)

        # text
        text_x = x2 - text_w - margin
        text_y = y1 + text_h + (margin // 2)
        cv2.putText(frame_bgr, now_str, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        return frame_bgr

    # ---- thread main loop ----
    def run(self):
        backoff = 0.5
        while not self._stopping:
            if self._cap is None or not self._cap.isOpened():
                if not self.rtsp_url:
                    # no URL, idle politely
                    self._emit_status(f"{self.name}: no URL configured")
                    time.sleep(0.5)
                    continue

                self._emit_status(f"{self.name}: connecting …")
                self._open()
                if not self._cap.isOpened():
                    self._emit_status(f"{self.name}: retry in {backoff:.1f}s")
                    time.sleep(backoff)
                    backoff = min(5.0, backoff * 1.6)
                    continue
                else:
                    self._emit_status(f"{self.name}: connected")
                    backoff = 0.5

            ok, frame = self._cap.read()
            if not ok or frame is None:
                self._emit_status(f"{self.name}: lost signal; reconnecting …")
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
                time.sleep(0.25)
                continue

            # overlay timestamp
            frame = self._overlay_timestamp(frame)

            # BGR -> RGB and to PIL.Image
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)

            if callable(self.on_frame):
                try:
                    self.on_frame(pil_img)
                except Exception:
                    pass

            # small sleep to be nice on CPU if stream is very fast
            time.sleep(0.005)

    def stop(self):
        self._stopping = True
        try:
            if self._cap:
                self._cap.release()
        except Exception:
            pass

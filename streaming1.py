from PyQt6 import QtCore, QtGui
import cv2
import datetime
import time

class VideoStreamWorker(QtCore.QThread):
    frameReady = QtCore.pyqtSignal(QtGui.QImage)
    statusChanged = QtCore.pyqtSignal(str)

    def __init__(self, rtsp_url: str, parent=None, name: str = "Camera"):
        super().__init__(parent)
        self.rtsp_url = rtsp_url
        self.name = name
        self._stopping = False
        self._cap = None
        self._last_status = ""

    def _emit_status(self, msg: str):
        if msg != self._last_status:
            self._last_status = msg
            self.statusChanged.emit(msg)

    def _open(self):
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
        # Use FFmpeg backend (default in many OpenCV builds)
        self._cap = cv2.VideoCapture(self.rtsp_url)
        # Reduce buffering for lower latency
        try:
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

    def run(self):
        backoff = 0.5
        while not self._stopping:
            if self._cap is None or not self._cap.isOpened():
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
                # Force reopen on next loop
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
                time.sleep(0.25)
                continue

            # Convert BGR -> RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)

            # Paint timestamp on top-right
            qimg = qimg.copy()
            painter = QtGui.QPainter(qimg)
            painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)

            # Semi-transparent background rectangle for readability
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            font = QtGui.QFont("Monospace", 12)
            font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
            painter.setFont(font)

            metrics = QtGui.QFontMetrics(font)
            text_width = metrics.horizontalAdvance(now_str)
            text_height = metrics.height()
            margin = 10
            rect = QtCore.QRect(qimg.width() - text_width - 2*margin - 2, margin,
                                text_width + 2*margin, text_height + margin//2)

            bg = QtGui.QColor(0, 0, 0, 128)
            fg = QtGui.QColor(255, 255, 255)
            painter.fillRect(rect, bg)
            painter.setPen(fg)
            painter.drawText(rect.adjusted(margin, 0, -margin, 0),
                             QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight,
                             now_str)
            painter.end()

            self.frameReady.emit(qimg)

            # small sleep to be nice on CPU if stream is very fast
            QtCore.QThread.msleep(5)

    def stop(self):
        self._stopping = True
        try:
            if self._cap:
                self._cap.release()
        except Exception:
            pass
        self.wait(1000)

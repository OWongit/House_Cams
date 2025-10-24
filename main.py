import cv2
import time
import threading
from datetime import datetime
import numpy as np

# ========= CONFIG =========
# Replace with your RTSP stream URLs
rtsp_url_1 = "rtsps://YOUR_STREAM"  # left
rtsp_url_2 = "rtsps://YOUR_STREAM"  # right

RETRY_SECONDS = 60
WINDOW_NAME = "RTSP Streams (Side-by-side)"
TARGET_HEIGHT = 540  # per-tile height before concatenation; adjust to taste
FONT = cv2.FONT_HERSHEY_SIMPLEX


# ========= UTIL / LOG =========
def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def open_capture(url: str):
    # Prefer FFMPEG backend when available
    backend = getattr(cv2, "CAP_FFMPEG", 0)
    cap = cv2.VideoCapture(url, backend)
    return cap


# ========= BACKGROUND READER =========
class RTSPStream:
    """
    Opens RTSP with OpenCV, continuously reads the latest frame in a thread,
    and attempts reconnect on failure with RETRY_SECONDS backoff.
    """

    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name
        self._frame = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.last_read_ts = 0.0
        self.status = "idle"

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2.0)

    def get_frame(self):
        with self._lock:
            return (None if self._frame is None else self._frame.copy(), self.status, self.last_read_ts)

    def _run(self):
        while not self._stop.is_set():
            cap = open_capture(self.url)
            if not cap.isOpened():
                self.status = "connecting..."
                log(f"{self.name}: Error: Could not open RTSP stream. Retrying in {RETRY_SECONDS} seconds...")
                cap.release()
                self._sleep_with_stop(RETRY_SECONDS)
                continue

            self.status = "LIVE"
            log(f"{self.name}: RTSP stream opened successfully.")

            while not self._stop.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    self.status = "dropped (reconnecting...)"
                    log(f"{self.name}: Error: Could not read frame. Retrying in {RETRY_SECONDS} seconds...")
                    break
                with self._lock:
                    self._frame = frame
                    self.last_read_ts = time.time()

            cap.release()
            self._sleep_with_stop(RETRY_SECONDS)

    def _sleep_with_stop(self, seconds: int):
        end = time.time() + seconds
        while not self._stop.is_set() and time.time() < end:
            time.sleep(0.2)


# ========= IMAGE HELPERS =========
def resize_to_height(img, target_h: int):
    h, w = img.shape[:2]
    if h == target_h:
        return img
    scale = target_h / float(h)
    new_w = max(1, int(w * scale))
    return cv2.resize(img, (new_w, target_h), interpolation=cv2.INTER_AREA)


def make_placeholder(text: str, w: int = 640, h: int = TARGET_HEIGHT):
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (w, 40), (64, 64, 64), thickness=-1)
    cv2.putText(canvas, text, (12, 28), FONT, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(canvas, "NO VIDEO", (12, h // 2), FONT, 1.0, (200, 200, 200), 2, cv2.LINE_AA)
    return canvas


def annotate(frame, header: str, status: str, stale: bool):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), thickness=-1)
    label = f"{header}  -  {status}" + ("  -  FROZEN" if stale else "")
    cv2.putText(frame, label, (12, 28), FONT, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return frame


# ========= WINDOW / LETTERBOX =========
def init_fullscreen_window(window_name: str):
    """
    Create a fullscreen window and return its (w, h) once the size is real.
    Ensures we can render onto our own black canvas to avoid white gutters.
    """
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | getattr(cv2, "WINDOW_FREERATIO", 0))
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Show a tiny black frame so the window manager finalizes the size.
    cv2.imshow(window_name, np.zeros((10, 10, 3), dtype=np.uint8))
    cv2.waitKey(1)

    win_w = win_h = 0
    for _ in range(20):
        try:
            _, _, w, h = cv2.getWindowImageRect(window_name)  # OpenCV 4+
            if w > 0 and h > 0:
                win_w, win_h = w, h
                break
        except Exception:
            pass
        cv2.waitKey(1)
        time.sleep(0.02)

    if win_w == 0 or win_h == 0:
        # Fallback to a sane default; the canvas will still be black
        win_w, win_h = 1920, 1080

    return win_w, win_h


def letterbox_to_size(img, out_w: int, out_h: int):
    """
    Create a black canvas (out_h, out_w) and center the image scaled-to-fit.
    """
    h, w = img.shape[:2]
    scale = min(out_w / float(w), out_h / float(h))
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)  # BLACK background
    y = (out_h - new_h) // 2
    x = (out_w - new_w) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


# ========= MAIN DISPLAY =========
def display_two_streams(url_left: str, url_right: str, name_left="FRONT", name_right="BACK"):
    stream_l = RTSPStream(url_left, name_left)
    stream_r = RTSPStream(url_right, name_right)

    stream_l.start()
    stream_r.start()

    # Create fullscreen and capture its true size once
    win_w, win_h = init_fullscreen_window(WINDOW_NAME)

    try:
        while True:
            frame_l, status_l, ts_l = stream_l.get_frame()
            frame_r, status_r, ts_r = stream_r.get_frame()

            now = time.time()
            stale_l = (now - ts_l) > 2.0 if ts_l > 0 else True
            stale_r = (now - ts_r) > 2.0 if ts_r > 0 else True

            if frame_l is None:
                frame_l = make_placeholder(f"{name_left} — {status_l}")
            else:
                frame_l = resize_to_height(frame_l, TARGET_HEIGHT)
                frame_l = annotate(frame_l, name_left, status_l, stale_l)

            if frame_r is None:
                frame_r = make_placeholder(f"{name_right} - {status_r}")
            else:
                frame_r = resize_to_height(frame_r, TARGET_HEIGHT)
                frame_r = annotate(frame_r, name_right, status_r, stale_r)

            mosaic = np.hstack([frame_l, frame_r])

            # If the window size changes (rare in fullscreen), adapt dynamically.
            try:
                _, _, w, h = cv2.getWindowImageRect(WINDOW_NAME)
                if w > 0 and h > 0 and (w != win_w or h != win_h):
                    win_w, win_h = w, h
            except Exception:
                pass

            out = letterbox_to_size(mosaic, win_w, win_h)
            cv2.imshow(WINDOW_NAME, out)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # q or ESC
                log("Exit requested by user.")
                break

    except KeyboardInterrupt:
        log("Interrupted by user. Exiting.")
    finally:
        stream_l.stop()
        stream_r.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    display_two_streams(rtsp_url_1, rtsp_url_2, "FRONT", "BACK")

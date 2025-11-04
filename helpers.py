import cv2
import time
import numpy as np
from datetime import datetime
from config import CONFIG

# ========= CONFIG =========
rtsp_url_1 = CONFIG["rtsp_url_1"]
rtsp_url_2 = CONFIG["rtsp_url_2"]
RETRY_SECONDS = CONFIG["RETRY_SECONDS"]
WINDOW_NAME = CONFIG["WINDOW_NAME"]
TARGET_HEIGHT = CONFIG["TARGET_HEIGHT"]
FONT = CONFIG["FONT"]


# ========= UTIL / LOG =========
def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def open_capture(url: str):
    # Prefer FFMPEG backend when available
    backend = getattr(cv2, "CAP_FFMPEG", 0)
    cap = cv2.VideoCapture(url, backend)
    return cap


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

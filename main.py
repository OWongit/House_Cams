import cv2
import time
import numpy as np
import helpers
from stream import RTSPStream
from config import CONFIG

# ========= CONFIG =========
rtsp_url_1 = CONFIG["rtsp_url_1"]
rtsp_url_2 = CONFIG["rtsp_url_2"]
RETRY_SECONDS = CONFIG["RETRY_SECONDS"]
WINDOW_NAME = CONFIG["WINDOW_NAME"]
TARGET_HEIGHT = CONFIG["TARGET_HEIGHT"]
FONT = CONFIG["FONT"]


# ========= MAIN DISPLAY =========
def display_streams(url_left: str, url_right: str, name_left="FRONT", name_right="BACK"):
    stream_l = RTSPStream(url_left, name_left)
    stream_r = RTSPStream(url_right, name_right)

    stream_l.start()
    stream_r.start()

    # Create fullscreen and capture its true size once
    win_w, win_h = helpers.init_fullscreen_window(WINDOW_NAME)

    try:
        while True:
            frame_l, status_l, ts_l = stream_l.get_frame()
            frame_r, status_r, ts_r = stream_r.get_frame()

            now = time.time()
            stale_l = (now - ts_l) > 2.0 if ts_l > 0 else True
            stale_r = (now - ts_r) > 2.0 if ts_r > 0 else True

            if frame_l is None:
                frame_l = helpers.make_placeholder(f"{name_left} - {status_l}")
            else:
                frame_l = helpers.resize_to_height(frame_l, TARGET_HEIGHT)
                frame_l = helpers.annotate(frame_l, name_left, status_l, stale_l)

            if frame_r is None:
                frame_r = helpers.make_placeholder(f"{name_right} - {status_r}")
            else:
                frame_r = helpers.resize_to_height(frame_r, TARGET_HEIGHT)
                frame_r = helpers.annotate(frame_r, name_right, status_r, stale_r)

            mosaic = np.hstack([frame_l, frame_r])

            # If the window size changes (rare in fullscreen), adapt dynamically.
            try:
                _, _, w, h = cv2.getWindowImageRect(WINDOW_NAME)
                if w > 0 and h > 0 and (w != win_w or h != win_h):
                    win_w, win_h = w, h
            except Exception:
                pass

            out = helpers.letterbox_to_size(mosaic, win_w, win_h)
            cv2.imshow(WINDOW_NAME, out)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                helpers.log("Exit requested by user.")
                break

    except KeyboardInterrupt:
        helpers.log("Interrupted by user. Exiting.")
    finally:
        stream_l.stop()
        stream_r.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    display_streams(rtsp_url_1, rtsp_url_2, "FRONT", "BACK")

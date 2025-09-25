import cv2
import time
from datetime import datetime

# Replace with your RTSP stream URL
rtsp_url = "rtsps://192.168.1.1:7441/jDhFy9De5o41cpFH?enableSrtp"

RETRY_SECONDS = 60
WINDOW_NAME = "RTSP Stream"


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def open_capture(url: str):
    # Prefer FFMPEG if available; fallback to default auto-detect
    backend = getattr(cv2, "CAP_FFMPEG", 0)
    cap = cv2.VideoCapture(url, backend)
    return cap


def display_stream(url: str):
    while True:
        cap = open_capture(url)

        if not cap.isOpened():
            log(f"Error: Could not open RTSP stream. Retrying in {RETRY_SECONDS} seconds...")
            cap.release()
            time.sleep(RETRY_SECONDS)
            continue

        log("RTSP stream opened successfully.")

        # Create window and force full screen
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            ret, frame = cap.read()

            # If the stream drops or a frame can't be read for any reason, break to retry
            if not ret or frame is None:
                log(f"Error: Could not read frame from stream. Retrying in {RETRY_SECONDS} seconds...")
                break

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # 'q' or ESC to quit
                log("Exit requested by user.")
                cap.release()
                cv2.destroyAllWindows()
                return

        # Clean up before retrying
        cap.release()
        cv2.destroyAllWindows()
        time.sleep(RETRY_SECONDS)


if __name__ == "__main__":
    try:
        display_stream(rtsp_url)
    except KeyboardInterrupt:
        log("Interrupted by user. Exiting.")
        cv2.destroyAllWindows()

import cv2
import time
from datetime import datetime

# Replace with your RTSP stream URL
rtsp_url = "rtsps://YOUR_RTSP_STREAM"

RETRY_SECONDS = 60
WINDOW_NAME = "RTSP Stream"


def log(msg: str) -> None:
    # Simple timestamped logger to stdout for visibility in console runs
    # Example output: [2025-09-24 12:34:56] RTSP stream opened successfully.
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def open_capture(url: str):
    # Construct a VideoCapture using the FFMPEG backend when available.
    # Many RTSP cameras/profiles are most reliable with FFMPEG.
    # If OpenCV was built without FFMPEG, CAP_FFMPEG may not exist (falls back to 0).
    backend = getattr(cv2, "CAP_FFMPEG", 0)
    cap = cv2.VideoCapture(url, backend)
    return cap


def display_stream(url: str):
    # Main loop that continuously attempts to open the RTSP stream,
    # and, once open, reads/plots frames until an error or user exit.
    while True:
        cap = open_capture(url)

        if not cap.isOpened():
            # Could not connect (network down, camera offline, bad URL, auth failure, etc.)
            # Back off for RETRY_SECONDS before trying again.
            log(f"Error: Could not open RTSP stream. Retrying in {RETRY_SECONDS} seconds...")
            cap.release()
            time.sleep(RETRY_SECONDS)
            continue

        log("RTSP stream opened successfully.")

        # Create a named window and force it into full screen mode.
        # WINDOW_NORMAL allows changing window size programmatically.
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            # Read a single frame from the stream.
            # ret: whether a frame was captured successfully
            # frame: the actual image buffer (numpy array) or None on failure
            ret, frame = cap.read()

            # If the stream drops mid-session, or a transient decode error occurs,
            # break out to the outer loop to reinitialize the connection after a delay.
            if not ret or frame is None:
                log(f"Error: Could not read frame from stream. Retrying in {RETRY_SECONDS} seconds...")
                break

            # Display the current frame in the fullscreen window.
            cv2.imshow(WINDOW_NAME, frame)

            # Poll for keypress every 1 ms to keep UI responsive.
            # Press 'q' or ESC (27) to cleanly exit the program.
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # 'q' or ESC to quit
                log("Exit requested by user.")
                cap.release()
                cv2.destroyAllWindows()
                return

        # If we reach here, an error occurred while reading frames.
        # Release the capture and close windows before sleeping/retrying.
        cap.release()
        cv2.destroyAllWindows()
        time.sleep(RETRY_SECONDS)


if __name__ == "__main__":
    # Allow Ctrl+C to terminate without an ugly traceback; ensure windows are closed.
    try:
        display_stream(rtsp_url)
    except KeyboardInterrupt:
        log("Interrupted by user. Exiting.")
        cv2.destroyAllWindows()

import cv2

CONFIG = {
    # Replace with your RTSP stream URLs
    "rtsp_url_1": "rtsps://192.168.1.1:7441/jDhFy9De5o41cpFH?enableSrtp",  # left
    "rtsp_url_2": "rtsps://192.168.1.1:7441/9GLfkjp10gO3LCTv?enableSrtp",  # right
    "RETRY_SECONDS": 60,
    "WINDOW_NAME": "RTSP Streams",
    "TARGET_HEIGHT": 540,  # per-tile height before concatenation; adjust to taste
    "FONT": cv2.FONT_HERSHEY_SIMPLEX,
}

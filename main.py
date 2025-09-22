import cv2
import numpy as np

# high qual
# rtsp_1 = "rtsps://192.168.1.1:7441/QcDlLIyfGCk792gp?enableSrtp"
# rtsp_2 = "rtsps://192.168.1.1:7441/lCXwveVuD96xmXcX?enableSrtp"

# low qual
rtsp_1 = "rtsps://192.168.1.1:7441/jDhFy9De5o41cpFH?enableSrtp"
rtsp_2 = "rtsps://192.168.1.1:7441/9GLfkjp10gO3LCTv?enableSrtp"

cap1 = cv2.VideoCapture(rtsp_1)
cap2 = cv2.VideoCapture(rtsp_2)

if not cap1.isOpened():
    print("Error: Could not open stream 1.")
if not cap2.isOpened():
    print("Error: Could not open stream 2.")
if not (cap1.isOpened() or cap2.isOpened()):
    raise SystemExit

window = "Dual RTSP"
cv2.namedWindow(window, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Target height for each pane (adjust if you like)
TARGET_H = 720
FONT = cv2.FONT_HERSHEY_SIMPLEX


def resize_keep_aspect(img, target_h):
    h, w = img.shape[:2]
    scale = target_h / float(h)
    new_w = max(1, int(w * scale))
    return cv2.resize(img, (new_w, target_h), interpolation=cv2.INTER_AREA)


def no_signal(width, height, label):
    slate = np.zeros((height, width, 3), dtype=np.uint8)
    text = f"{label}: No signal"
    (tw, th), _ = cv2.getTextSize(text, FONT, 1.0, 2)
    cv2.putText(slate, text, ((width - tw) // 2, (height + th) // 2), FONT, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    return slate


last1, last2 = None, None

while True:
    ok1, f1 = cap1.read()
    ok2, f2 = cap2.read()

    if ok1:
        last1 = f1
    if ok2:
        last2 = f2

    # If neither stream can provide a frame, bail
    if last1 is None and last2 is None:
        print("Error: Neither stream is providing frames.")
        break

    # Prepare frames (or slates) at a common height
    if last1 is None:
        f1r = resize_keep_aspect(no_signal(640, TARGET_H, "Stream 1"), TARGET_H)
    else:
        f1r = resize_keep_aspect(last1, TARGET_H)

    if last2 is None:
        f2r = resize_keep_aspect(no_signal(640, TARGET_H, "Stream 2"), TARGET_H)
    else:
        f2r = resize_keep_aspect(last2, TARGET_H)

    # Concatenate side-by-side
    combined = cv2.hconcat([f1r, f2r])

    cv2.imshow(window, combined)
    key = cv2.waitKey(1) & 0xFF
    if key in (ord("q"), 27):  # q or ESC
        break

cap1.release()
cap2.release()
cv2.destroyAllWindows()

# camera_test.py
import sys
import time
import cv2
import numpy as np
from config import CONFIG

W, H = 640, 480

# ---- camera source: Pi camera (picamera2) first, USB webcam as fallback ----
picam = None
cap = None
try:
    from picamera2 import Picamera2
    picam = Picamera2()
    picam.configure(picam.create_preview_configuration(
        main={"size": (W, H), "format": "RGB888"}))  # RGB888 = BGR order for OpenCV
    picam.start()
    print("Using Pi camera (picamera2)")
except Exception as e:
    print(f"picamera2 unavailable ({e}), trying USB camera...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    if not cap.isOpened():
        sys.exit("No camera found.")


def grab():
    if picam is not None:
        return picam.capture_array()
    ok, frame = cap.read()
    return frame if ok else None


threshold = CONFIG.line_threshold
roi_y = CONFIG.roi_y
ROI_H = 100
headless = False
last_save = 0.0

print("Keys: q quit | s snapshot | -/= threshold | [/] move ROI up/down")

try:
    while True:
        frame = grab()
        if frame is None:
            continue
        h, w = frame.shape[:2]
        y0 = max(0, min(roi_y, h - 20))
        y1 = min(h, y0 + ROI_H)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        mask = (gray < threshold).astype(np.uint8) * 255

        # ---- line detection inside the ROI (same idea as line following) ----
        roi_mask = mask[y0:y1]
        ys, xs = np.nonzero(roi_mask)
        if len(xs) > 50:
            cx = float(xs.mean())
            error = (cx - w / 2) / (w / 2)          # -1 (left) .. +1 (right)
            status = f"line x={cx:.0f}  error={error:+.2f}"
            cv2.circle(frame, (int(cx), (y0 + y1) // 2), 8, (0, 255, 0), -1)
            # line tilt: compare centroid of top half vs bottom half of ROI
            mid = len(roi_mask) // 2
            t = np.nonzero(roi_mask[:mid])[1]
            b = np.nonzero(roi_mask[mid:])[1]
            if len(t) > 20 and len(b) > 20:
                status += f"  tilt={t.mean() - b.mean():+.0f}px"
        else:
            status = "NO LINE in ROI"

        # ---- overlay: mask tint, ROI band, center guides ----
        frame[mask > 0] = (0.5 * frame[mask > 0] + 0.5 * np.array([0, 0, 255])).astype(np.uint8)
        cv2.rectangle(frame, (0, y0), (w - 1, y1), (255, 255, 0), 2)
        cv2.line(frame, (w // 2, 0), (w // 2, h), (255, 255, 255), 1)       # robot centerline
        cv2.line(frame, (0, h // 2), (w, h // 2), (255, 255, 255), 1)       # level reference
        for frac in (0.25, 0.75):
            cv2.line(frame, (int(w * frac), 0), (int(w * frac), h), (120, 120, 120), 1)

        cv2.putText(frame, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"thr={threshold} roi_y={roi_y}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if not headless:
            try:
                cv2.imshow("camera test", frame)
                key = cv2.waitKey(1) & 0xFF
            except cv2.error:
                headless = True
                print("No display; saving preview.jpg once per second instead.")
                key = 255
        else:
            now = time.time()
            if now - last_save > 1.0:
                cv2.imwrite("preview.jpg", frame)
                print(status)
                last_save = now
            time.sleep(0.05)
            key = 255

        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite("snapshot.jpg", frame)
            print("saved snapshot.jpg")
        elif key == ord("-"):
            threshold = max(0, threshold - 5)
        elif key == ord("="):
            threshold = min(255, threshold + 5)
        elif key == ord("["):
            roi_y = max(0, roi_y - 10)
        elif key == ord("]"):
            roi_y = min(h - 20, roi_y + 10)
finally:
    if picam is not None:
        picam.stop()
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print(f"\nFinal values -> line_threshold={threshold}, roi_y={roi_y}")
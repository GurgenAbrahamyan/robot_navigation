"""Line position and steering calculation. Expects a BGR camera frame."""
import cv2
import numpy as np


def line_mask(frame, threshold=80, roi_y=300):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi = gray[roi_y:, :]
    # Dark line on a light floor => line pixels become white in the mask.
    _, mask = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask, roi_y


def row_center(mask, y, min_pixels=4):
    if y < 0 or y >= mask.shape[0]:
        return None
    xs = np.where(mask[y] > 0)[0]
    if len(xs) < min_pixels:
        return None
    return int(np.median(xs))


def line_error_and_steering(frame, kp=0.65, threshold=80, roi_y=300):
    mask, offset = line_mask(frame, threshold, roi_y)
    h, w = mask.shape
    near = row_center(mask, min(h - 1, int(h * 0.78)))
    far = row_center(mask, min(h - 1, int(h * 0.30)))

    if near is None and far is None:
        return {"found": False, "mask": mask, "near": None, "far": None,
                "error": None, "steering": 0.0}

    # If only one row sees the line, use it. Otherwise weight the near row more.
    center = w / 2
    near_error = (near - center) / center if near is not None else None
    far_error = (far - center) / center if far is not None else None
    if near_error is not None and far_error is not None:
        error = 0.7 * near_error + 0.3 * far_error
    else:
        error = near_error if near_error is not None else far_error

    steering = max(-1.0, min(1.0, kp * error))
    return {"found": True, "mask": mask, "near": near, "far": far,
            "error": error, "steering": steering}

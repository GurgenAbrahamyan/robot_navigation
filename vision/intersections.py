"""Simple intersection classifier for a binary mask.

The mask must have line pixels as white (255), background black (0).
This is a baseline heuristic and must be tuned on actual field footage.
"""
import numpy as np


def _has_line(mask, x0, x1, y0, y1, min_pixels=5):
    region = mask[y0:y1, x0:x1]
    return int(np.count_nonzero(region)) >= min_pixels


def classify_intersection(mask):
    h, w = mask.shape
    # Look near the bottom of the ROI where the robot is approaching the junction.
    y0, y1 = int(h * 0.45), int(h * 0.85)
    mid0, mid1 = int(w * 0.40), int(w * 0.60)
    left0, left1 = int(w * 0.05), int(w * 0.38)
    right0, right1 = int(w * 0.62), int(w * 0.95)

    center = _has_line(mask, mid0, mid1, y0, y1)
    left = _has_line(mask, left0, mid0, y0, y1)
    right = _has_line(mask, mid1, right1, y0, y1)

    if center and left and right:
        return "cross"
    if center and left:
        return "left_or_t"
    if center and right:
        return "right_or_t"
    if left and right and not center:
        return "wide_junction"
    return None


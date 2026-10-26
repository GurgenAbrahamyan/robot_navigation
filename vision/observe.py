"""One camera frame -> one Observation (everything the navigator needs)."""
from dataclasses import dataclass
from typing import Optional

from vision.intersections import classify_intersection
from vision.line_following import line_error_and_steering


@dataclass
class Observation:
    found: bool = False                # a line is visible
    steering: float = 0.0              # -1..1, positive = steer right
    error: Optional[float] = None      # normalized offset of the line, +right
    junction: Optional[str] = None     # 'cross' | 'left_or_t' | 'right_or_t' | 'wide_junction'


def observe(frame, cfg) -> Observation:
    r = line_error_and_steering(frame, kp=cfg.kp, threshold=cfg.line_threshold, roi_y=cfg.roi_y)
    if not r["found"]:
        return Observation(found=False)
    mask = r["mask"]
    return Observation(
        found=True,
        steering=r["steering"],
        error=r["error"],
        junction=classify_intersection(mask),
    )

"""All wiring and calibration numbers live here. Nothing else needs editing
to adapt the robot, except course.py (the command sequence).

Values marked CALIBRATE are guesses: measure them on the real robot/floor.
Values marked WIRING are placeholders: set them to your actual BCM pins.
"""
from dataclasses import dataclass


@dataclass
class Config:
    # ---- WIRING (BCM pin numbers) -------------------------------------
    # Dual H-bridge (L298N / TB6612 style): (forward_pin, backward_pin, pwm_enable_pin)
    left_pins: tuple = (5, 6, 12)
    right_pins: tuple = (13, 19, 26)
    left_invert: bool = True      # flip if that wheel spins the wrong way
    right_invert: bool = True
    pusher_servo_pin: int = 18     # servo for button/cube mechanism

    # ---- SPEEDS (0..1) ---------------------------------------------------
    cruise_speed: float = 0.40
    creep_speed: float = 0.30
    turn_speed: float = 0.35

    # ---- LINE FOLLOWING / VISION ---------------------------------------
    line_threshold: int = 80       # gray < this => line (dark line, light floor)
    roi_y: int = 300
    kp: float = 0.65

    # ---- CALIBRATE: motion ------------------------------------------------
    turn_rate_deg_s: float = 150.0     # in-place rotation rate at turn_speed
    turn_open_loop_fraction: float = 0.70   # spin blindly this much, then look for the line
    seek_timeout_s: float = 4.0        # give up looking for the line after a turn
    center_tolerance: float = 0.20     # |error| below this counts as "line centered"
    junction_advance_s: float = 0.25   # roll forward so wheels' pivot sits on the junction
    straight_cross_s: float = 0.45     # 'straight' command: roll across a junction
    dead_end_advance_s: float = 0.0    # extra roll after line disappears at a dead end

    # ---- Leg (forward) behaviour ---------------------------------------
    rearm_frames: int = 6              # frames w/o junction before events re-arm
    lost_frames: int = 8               # consecutive no-line frames => dead end
    max_leg_s: float = 40.0            # safety: abort a forward leg after this long
    loop_hz: float = 30.0

    # ---- CALIBRATE: tasks (open-loop, no sensors yet) -----------------
    button_extend_s: float = 0.6
    button_hold_s: float = 0.4
    cube_push_s: float = 1.2
    cube_retreat_s: float = 1.0
    park_advance_s: float = 0.8
    park_hold_s: float = 5.5           # rule: >= 5 s inside the zone

    # If True, a task that returns False aborts the course.
    halt_on_failed_task: bool = True


CONFIG = Config()

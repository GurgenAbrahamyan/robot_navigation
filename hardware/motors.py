"""Differential-drive motor driver.

Two backends share one interface:
  * GpioBackend - real hardware through gpiozero (Raspberry Pi)
  * SimBackend  - prints/records commands; used by --demo and the tests
"""
import time

from config import CONFIG


def _clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, float(x)))


class SimBackend:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.log = []          # (left, right) history

    def drive(self, left, right):
        self.log.append((round(left, 3), round(right, 3)))
        if self.verbose:
            print(f"[MOTOR] L={left:+.2f} R={right:+.2f}")


class GpioBackend:
    def __init__(self, cfg):
        from gpiozero import Motor  # imported lazily: only exists on the Pi
        self._left = Motor(forward=cfg.left_pins[0], backward=cfg.left_pins[1], enable=cfg.left_pins[2])
        self._right = Motor(forward=cfg.right_pins[0], backward=cfg.right_pins[1], enable=cfg.right_pins[2])
        self._li = -1 if cfg.left_invert else 1
        self._ri = -1 if cfg.right_invert else 1

    @staticmethod
    def _set(motor, v):
        if v > 0:
            motor.forward(min(1.0, v))
        elif v < 0:
            motor.backward(min(1.0, -v))
        else:
            motor.stop()

    def drive(self, left, right):
        self._set(self._left, left * self._li)
        self._set(self._right, right * self._ri)


class Motors:
    def __init__(self, cfg=CONFIG, demo=False, backend=None, sleep=time.sleep):
        self.cfg = cfg
        self.sleep = sleep
        self.backend = backend or (SimBackend() if demo else GpioBackend(cfg))

    # -- low level ------------------------------------------------------
    def drive(self, left, right):
        self.backend.drive(_clamp(left), _clamp(right))

    def stop(self):
        self.drive(0.0, 0.0)

    # -- simple moves ---------------------------------------------------
    def forward(self, speed=None, duration=None):
        s = self.cfg.cruise_speed if speed is None else speed
        self.drive(s, s)
        if duration is not None:
            self.sleep(duration)
            self.stop()

    def backward(self, speed=None, duration=None):
        s = self.cfg.creep_speed if speed is None else speed
        self.drive(-s, -s)
        if duration is not None:
            self.sleep(duration)
            self.stop()

    def steer(self, steering, speed=None):
        """steering in [-1, 1]; positive = line is to the right => turn right."""
        s = self.cfg.cruise_speed if speed is None else speed
        k = _clamp(steering)
        self.drive(s * (1 + k), s * (1 - k))

    # -- in-place rotation ----------------------------------------------
    def spin(self, direction, speed=None):
        """Start rotating in place. direction: 'left' or 'right'. Non-blocking."""
        s = self.cfg.turn_speed if speed is None else speed
        if direction == "left":
            self.drive(-s, s)
        elif direction == "right":
            self.drive(s, -s)
        else:
            raise ValueError(direction)

    def spin_degrees(self, direction, degrees, speed=None):
        """Open-loop timed rotation (accuracy depends on turn_rate_deg_s calibration)."""
        self.spin(direction, speed)
        self.sleep(abs(degrees) / self.cfg.turn_rate_deg_s)
        self.stop()

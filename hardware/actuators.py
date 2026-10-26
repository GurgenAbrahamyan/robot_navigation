"""Mechanism hooks for the tasks (button pusher servo etc.).

Replace the bodies once the real mechanism exists. Everything is open-loop for
now: there is no feedback telling us a task actually succeeded.
"""
from config import CONFIG


class SimServo:
    def __init__(self):
        self.position = 0.0

    def move(self, pos):
        self.position = pos
        print(f"[SERVO] position={pos}")


class GpioServo:
    def __init__(self, pin):
        from gpiozero import Servo
        self._servo = Servo(pin)

    def move(self, pos):  # pos in [-1, 1]
        self._servo.value = max(-1.0, min(1.0, pos))


class Actuators:
    def __init__(self, cfg=CONFIG, demo=False, sleep=None):
        import time
        self.cfg = cfg
        self.sleep = sleep or time.sleep
        self.pusher = SimServo() if demo else GpioServo(cfg.pusher_servo_pin)

    def press_button(self):
        self.pusher.move(1.0)
        self.sleep(self.cfg.button_extend_s)
        self.sleep(self.cfg.button_hold_s)
        self.pusher.move(-1.0)
        self.sleep(self.cfg.button_extend_s)

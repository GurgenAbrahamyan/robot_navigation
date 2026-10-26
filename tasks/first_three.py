"""Task routines 1-3. Open-loop: they perform the physical action but cannot
verify it. Each returns True when the action finished; swap in sensor/camera
verification where the TODOs are."""
from config import CONFIG


class Tasks:
    def __init__(self, motors, actuators, cfg=CONFIG, sleep=None):
        import time
        self.motors = motors
        self.act = actuators
        self.cfg = cfg
        self.sleep = sleep or time.sleep

    def server_boot_up(self):
        """Task 1: robot is at the end of the server stub line; press the button."""
        self.motors.stop()
        print("[TASK 1] Server Boot-Up: pressing button (UNVERIFIED, open-loop)")
        self.act.press_button()
        # TODO: confirm indicator went red -> green before returning True.
        return True

    def maintenance_gate(self):
        """Task 2: push the cube onto the pressure pad, then back off."""
        self.motors.stop()
        print("[TASK 2] Maintenance Gate: pushing cube (UNVERIFIED, open-loop)")
        self.motors.forward(self.cfg.creep_speed, self.cfg.cube_push_s)
        self.motors.backward(self.cfg.creep_speed, self.cfg.cube_retreat_s)
        # TODO: confirm the gate opened (limit switch / camera); the 20 s window starts then.
        return True

    def charging_stop(self):
        """Task 3: roll into the zone and stay put for > 5 s."""
        print("[TASK 3] Charging Stop: parking (UNVERIFIED, open-loop)")
        self.motors.forward(self.cfg.creep_speed, self.cfg.park_advance_s)
        self.motors.stop()
        self.sleep(self.cfg.park_hold_s)
        # TODO: confirm the robot is fully inside the zone before returning True.
        return True

    def run(self, number):
        methods = {1: self.server_boot_up, 2: self.maintenance_gate, 3: self.charging_stop}
        if number not in methods:
            raise ValueError(f"Task {number} is not implemented")
        return methods[number]()

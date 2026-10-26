"""Executes a parsed course one command at a time (blocking)."""
import time

from config import CONFIG
from navigation.commands import TURN_DEGREES, parse_course


class RunError(RuntimeError):
    pass


class Runner:
    def __init__(self, motors, perception, tasks, cfg=CONFIG, sleep=time.sleep, clock=time.monotonic):
        self.motors = motors
        self.perception = perception
        self.tasks = tasks
        self.cfg = cfg
        self.sleep = sleep
        self.clock = clock
        self.period = 1.0 / cfg.loop_hz

    # ---- public -------------------------------------------------------
    def run(self, course):
        commands = parse_course(course)
        try:
            for i, cmd in enumerate(commands):
                print(f"[RUN] {i + 1}/{len(commands)}: {cmd.source or cmd.name}")
                self._execute(cmd)
            print("[RUN] course complete")
        except BaseException:
            self.motors.stop()
            raise
        finally:
            self.motors.stop()

    # ---- dispatch -----------------------------------------------------
    def _execute(self, cmd):
        n = cmd.name
        if n == "forward":
            self.perception.notify("forward")
            self._follow_line()
        elif n in TURN_DEGREES:
            self.perception.notify("turn")
            self._turn("left" if n == "turn_around" else n, TURN_DEGREES[n])
        elif n == "straight":
            self.motors.forward(self.cfg.creep_speed, self.cfg.straight_cross_s)
        elif n == "task":
            self.perception.notify("task")
            self.motors.stop()
            ok = self.tasks.run(int(cmd.arg))
            if not ok and self.cfg.halt_on_failed_task:
                raise RunError(f"task {int(cmd.arg)} reported failure")
        elif n == "wait":
            self.motors.stop()
            self.sleep(cmd.arg)
        elif n == "stop":
            self.motors.stop()
        else:
            raise RunError(f"unhandled command {n}")

    # ---- forward: line following until an event -----------------------
    def _follow_line(self):
        cfg = self.cfg
        armed_clear = 0          # consecutive frames with no junction
        armed = False
        lost = 0
        seen_line = False
        start = self.clock()
        while True:
            if self.clock() - start > cfg.max_leg_s:
                raise RunError("forward leg timed out (line never ended)")
            obs = self.perception.read()

            if not obs.found:
                lost += 1
                if lost >= cfg.lost_frames:
                    if not seen_line:
                        raise RunError("no line visible at start of forward leg")
                    print("[NAV] dead end")
                    if cfg.dead_end_advance_s > 0:
                        self.motors.forward(cfg.creep_speed, cfg.dead_end_advance_s)
                    self.motors.stop()
                    return
                self.motors.stop()   # brief loss: wait for it to come back
                self.sleep(self.period)
                continue
            lost = 0
            seen_line = True

            event = obs.junction
            if event is None:
                armed_clear += 1
                if armed_clear >= cfg.rearm_frames:
                    armed = True
            else:
                armed_clear = 0
                if armed:
                    print(f"[NAV] reached {event}")
                    self.motors.forward(cfg.creep_speed, cfg.junction_advance_s)
                    self.motors.stop()
                    return

            self.motors.steer(obs.steering)
            self.sleep(self.period)

    # ---- turning ------------------------------------------------------
    def _turn(self, direction, degrees):
        cfg = self.cfg
        self.motors.spin_degrees(direction, degrees * cfg.turn_open_loop_fraction)
        # Creep around slowly until the new line is under the camera center.
        self.motors.spin(direction, cfg.turn_speed * 0.7)
        start = self.clock()
        while True:
            obs = self.perception.read()
            if obs.found and obs.error is not None and abs(obs.error) <= cfg.center_tolerance:
                self.motors.stop()
                return
            if self.clock() - start > cfg.seek_timeout_s:
                self.motors.stop()
                raise RunError(f"lost: no line found after turning {direction}")
            self.sleep(self.period)

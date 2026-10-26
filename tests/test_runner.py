import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import contextlib
import numpy as np, cv2

from config import Config
from course import COURSE
from hardware.actuators import Actuators
from hardware.motors import Motors, SimBackend
from navigation.commands import parse_course
from navigation.perception import ScriptedPerception
from navigation.runner import RunError, Runner
from tasks.first_three import Tasks
from vision.observe import observe


@contextlib.contextmanager
def raises(exc):
    try:
        yield type("Info", (), {})
    except exc as e:
        raises.last = e
        return
    raise AssertionError(f"{exc.__name__} not raised")


def make(events, cfg=None):
    cfg = cfg or Config()
    sleeps = []
    sl = sleeps.append
    t = [0.0]
    def clock():
        t[0] += 0.01
        return t[0]
    backend = SimBackend(verbose=False)
    motors = Motors(cfg, backend=backend, sleep=sl)
    act = Actuators(cfg, demo=True, sleep=sl)
    tasks = Tasks(motors, act, cfg, sleep=sl)
    perc = ScriptedPerception(events)
    return Runner(motors, perc, tasks, cfg, sleep=sl, clock=clock), backend, sleeps


def test_parse_expands_aliases():
    names = [c.name for c in parse_course(["left_forward", "stop_task_3"])]
    assert names == ["left", "forward", "forward", "task", "stop"]


def test_parse_rejects_typos_before_moving():
    with raises(ValueError):
        parse_course(["forward", "lefft", "task_9"])
    assert "lefft" in str(raises.last) and "task_9" in str(raises.last)


def test_full_course_runs_and_ends_stopped():
    n_forward = sum(c.name == "forward" for c in parse_course(COURSE))
    r, backend, sleeps = make(["junction"] * n_forward)
    r.run(COURSE)
    assert backend.log[-1] == (0.0, 0.0)
    assert r.perception.events == []          # every forward leg consumed
    assert max(sleeps) >= 5.5                 # task 3 hold


def test_dead_end_ends_leg():
    r, backend, _ = make(["dead_end"])
    r.run(["forward"])
    assert backend.log[-1] == (0.0, 0.0)


def test_turn_without_line_aborts():
    cfg = Config(seek_timeout_s=0.05)
    r, backend, _ = make([])
    r.cfg = cfg
    r.perception.read = lambda: __import__("vision.observe", fromlist=["x"]).Observation(found=False)
    with raises(RunError):
        r.run(["left"])
    assert backend.log[-1] == (0.0, 0.0)


def test_turn_directions_drive_wheels_correctly():
    r, backend, _ = make([])
    r.run(["left"])
    assert (-0.35, 0.35) in backend.log        # left wheel back, right wheel forward
    backend.log.clear()
    r.run(["right"])
    assert (0.35, -0.35) in backend.log


# ---- vision on synthetic frames --------------------------------------
def frame(draw):
    img = np.full((480, 640, 3), 230, np.uint8)
    draw(img)
    return img


def test_vision_straight_line_is_not_junction():
    f = frame(lambda im: cv2.line(im, (320, 480), (320, 300), (0, 0, 0), 18))
    o = observe(f, Config())
    assert o.found and o.junction is None and abs(o.error) < 0.1


def test_vision_cross_junction():
    def d(im):
        cv2.line(im, (320, 480), (320, 300), (0, 0, 0), 18)
        cv2.line(im, (0, 400), (640, 400), (0, 0, 0), 18)
    o = observe(frame(d), Config())
    assert o.junction == "cross"


def test_vision_left_bend_registers_as_junction():
    def d(im):
        cv2.line(im, (340, 480), (340, 400), (0, 0, 0), 18)
        cv2.line(im, (340, 400), (60, 400), (0, 0, 0), 18)
    assert observe(frame(d), Config()).junction == "left_or_t"


def test_vision_steering_sign():
    f = frame(lambda im: cv2.line(im, (500, 480), (500, 300), (0, 0, 0), 18))
    assert observe(f, Config()).steering > 0     # line on the right => steer right


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print("PASS", name)
            except Exception as e:
                failed += 1; print("FAIL", name, repr(e))
    sys.exit(1 if failed else 0)

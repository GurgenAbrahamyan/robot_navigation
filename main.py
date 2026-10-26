"""Entry point.

  python3 main.py --demo            simulated motors + scripted world (no hardware)
  python3 main.py                   real robot, runs course.COURSE
  python3 main.py --course a,b,c    run an ad-hoc comma-separated sequence
"""
import argparse
import time

from config import CONFIG
from course import COURSE
from hardware.actuators import Actuators
from hardware.motors import Motors
from navigation.commands import parse_course
from navigation.perception import CameraPerception, ScriptedPerception
from navigation.runner import Runner
from tasks.first_three import Tasks


def build(demo):
    motors = Motors(CONFIG, demo=demo)
    act = Actuators(CONFIG, demo=demo)
    tasks = Tasks(motors, act, CONFIG)
    if demo:
        perception = ScriptedPerception(["junction"] * 50)
    else:
        perception = CameraPerception(CONFIG)
        time.sleep(1)  # camera warm-up
    return Runner(motors, perception, tasks, CONFIG), perception


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true", help="simulate everything")
    p.add_argument("--course", help="comma-separated commands instead of course.py")
    p.add_argument("--check", action="store_true", help="only validate the course")
    args = p.parse_args()

    course = [c.strip() for c in args.course.split(",")] if args.course else COURSE
    parse_course(course)  # fail early on typos
    if args.check:
        print(f"OK: {len(course)} commands valid")
        return
    runner, perception = build(args.demo)
    try:
        runner.run(course)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        runner.motors.stop()
        perception.close()


if __name__ == "__main__":
    main()

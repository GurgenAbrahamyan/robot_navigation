"""Turns the course (a list of strings) into validated commands.

Vocabulary
  forward       follow the line until the next junction/bend or dead end, then stop on it
  left / right  rotate in place ~90 deg at the current spot until the new line is centered
  turn_around   rotate ~180 deg until the line behind us is centered
  straight      roll across the junction we are on (no turn), ready for the next 'forward'
  left_forward  = left, forward         (ALIASES below; edit if you mean something else)
  right_forward = right, forward
  task_1/2/3    run that task
  stop_task_3   = forward, task_3, stop (final parking)
  wait_<sec>    pause, e.g. wait_2.5
  stop          stop motors
"""
import re
from dataclasses import dataclass

ALIASES = {
    "left_forward": ["left", "forward"],
    "right_forward": ["right", "forward"],
    "stop_task_3": ["forward", "task_3", "stop"],
}

TURN_DEGREES = {"left": 90, "right": 90, "turn_around": 180}
SIMPLE = {"forward", "left", "right", "turn_around", "straight", "stop"}


@dataclass(frozen=True)
class Command:
    name: str          # forward | left | right | turn_around | straight | stop | task | wait
    arg: float = 0.0   # task number or seconds
    source: str = ""   # original string, for messages


def parse_course(course):
    """Validate the whole course up front so a typo fails before the robot moves."""
    commands, errors = [], []
    for i, raw in enumerate(course):
        text = str(raw).strip().lower()
        expanded = ALIASES.get(text, [text])
        for item in expanded:
            m_task = re.fullmatch(r"task_(\d+)", item)
            m_wait = re.fullmatch(r"wait_(\d+(?:\.\d+)?)", item)
            if item in SIMPLE:
                commands.append(Command(item, 0.0, raw))
            elif m_task and int(m_task.group(1)) in (1, 2, 3):
                commands.append(Command("task", int(m_task.group(1)), raw))
            elif m_wait:
                commands.append(Command("wait", float(m_wait.group(1)), raw))
            else:
                errors.append(f"#{i}: unknown command {raw!r}")
    if errors:
        raise ValueError("Bad course:\n  " + "\n  ".join(errors))
    return commands

# Robot navigation: run any command sequence

Edit `course.py`, then run `python3 main.py` on the Pi. Try it without hardware: `python3 main.py --demo`.
Validate a course only: `python3 main.py --check`. Ad hoc: `python3 main.py --course forward,left,forward,task_1`.

## Commands
| command | meaning |
|---|---|
| `forward` | follow the line until a junction/bend or a dead end, then stop on it |
| `left` / `right` | rotate ~90° in place, then keep rotating until the new line is centered |
| `turn_around` | rotate ~180° until the line behind is centered |
| `straight` | roll across the current junction without turning |
| `left_forward` / `right_forward` | shorthand for `left, forward` (see `ALIASES` in `navigation/commands.py`) |
| `task_1/2/3` | run that task |
| `stop_task_3` | shorthand for `forward, task_3, stop` |
| `wait_<sec>`, `stop` | pause / stop motors |

The whole course is validated before the robot moves. On any failure (line lost, timeout, task failure) the motors stop.

## Before first real run
1. `config.py`: set the WIRING pins, then check wheel directions (`left_invert` / `right_invert`).
2. Calibrate (`config.py`, marked CALIBRATE): `turn_rate_deg_s`, `junction_advance_s`, task timings.
3. Tune `line_threshold` / `roi_y` on real field footage.
4. Tasks are open-loop: they do the action but cannot confirm it worked.

Tests: `python3 tests/test_runner.py` (also works with pytest).

# wheel_test.py
from time import sleep
from gpiozero import Motor
from config import CONFIG

TEST_SPEED = 0.5   # raise if the wheel doesn't move (L298N loses ~2V)
RUN_S = 1.5


def make(pins):
    fwd, bwd, en = pins
    return Motor(forward=fwd, backward=bwd, enable=en, pwm=True)


def run(name, motor, invert):
    print(f"\n--- {name} wheel: FORWARD for {RUN_S}s ---")
    input("Press Enter to start...")
    (motor.backward if invert else motor.forward)(TEST_SPEED)
    sleep(RUN_S)
    motor.stop()
    sleep(0.5)

    print(f"--- {name} wheel: BACKWARD for {RUN_S}s ---")
    (motor.forward if invert else motor.backward)(TEST_SPEED)
    sleep(RUN_S)
    motor.stop()


left = make(CONFIG.left_pins)
right = make(CONFIG.right_pins)

try:
    run("LEFT", left, CONFIG.left_invert)
    run("RIGHT", right, CONFIG.right_invert)

    print("\n--- BOTH wheels FORWARD (robot should drive straight) ---")
    input("Press Enter to start...")
    for m, inv in ((left, CONFIG.left_invert), (right, CONFIG.right_invert)):
        (m.backward if inv else m.forward)(TEST_SPEED)
    sleep(RUN_S)
finally:
    left.stop()
    right.stop()
    left.close()
    right.close()
    print("\nDone.")
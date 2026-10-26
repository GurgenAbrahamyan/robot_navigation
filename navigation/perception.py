"""Perception sources: the real camera, and a scripted one for tests/demo."""
from vision.observe import Observation, observe


class CameraPerception:
    def __init__(self, cfg):
        from picamera2 import Picamera2
        import cv2
        self._cv2 = cv2
        self.cfg = cfg
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"}))
        self.camera.start()

    def notify(self, command_name):
        pass

    def read(self) -> Observation:
        frame = self._cv2.cvtColor(self.camera.capture_array(), self._cv2.COLOR_RGB2BGR)
        return observe(frame, self.cfg)

    def close(self):
        self.camera.stop()


class ScriptedPerception:
    """Fake world for --demo and tests.

    `events` is the list of things each 'forward' leg ends with, in order, e.g.
    ['junction', 'dead_end', ...]. Turns are answered with a couple of
    off-line frames and then a centered line.
    """
    def __init__(self, events, line_frames=8):
        self.events = list(events)
        self.line_frames = line_frames
        self._kind = None
        self._n = 0
        self._leg_event = None

    def notify(self, command_name):
        self._kind = command_name
        self._n = 0
        if command_name == "forward":
            if not self.events:
                raise RuntimeError("ScriptedPerception ran out of leg events")
            self._leg_event = self.events.pop(0)

    def read(self) -> Observation:
        self._n += 1
        if self._kind == "forward":
            # first frames: still sitting on the junction we just left (must be ignored)
            if self._n <= 2:
                return Observation(found=True, error=0.0, junction="cross")
            if self._n <= 2 + self.line_frames:
                return Observation(found=True, error=0.05)
            ev = self._leg_event
            if ev == "dead_end":
                return Observation(found=False)
            return Observation(found=True, error=0.0, junction="left_or_t")
        if self._kind == "turn":
            if self._n <= 2:
                return Observation(found=False)
            return Observation(found=True, error=0.0)
        return Observation(found=True, error=0.0)

    def close(self):
        pass

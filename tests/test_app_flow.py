import numpy as np
import pytest
from motion_app.app import AlertState, Application
from motion_app.config import Config
from motion_app.motion_detector import MotionDetector


class FakeCamera:
    def __init__(self, failure=None):
        self.failure = failure
        self.released = False
        self.reads = 0

    def open(self):
        if self.failure == 'open':
            raise RuntimeError('open failed')

    def read(self):
        self.reads += 1
        if self.failure == 'read':
            raise RuntimeError('read failed')
        if self.failure == 'invalid':
            return None
        return np.zeros((40, 50, 3), np.uint8)

    def release(self):
        self.released = True
        if self.failure == 'release':
            raise RuntimeError('release failed')


class FakeDisplay:
    def __init__(self, failure=None):
        self.failure = failure
        self.closed = False
        self.alerts = []

    def open(self):
        self.check('open')

    def check(self, operation):
        if self.failure == operation:
            raise RuntimeError(operation + ' failed')
        if self.failure == 'interrupt' and operation == 'poll':
            raise KeyboardInterrupt

    def render(self, frame, alert, boxes):
        self.check('render')
        self.alerts.append(alert)
        return frame.copy()

    def show(self, frame):
        self.check('show')

    def poll_quit(self):
        self.check('poll')
        return True

    def close(self):
        self.closed = True
        self.check('close')


@pytest.mark.parametrize('camera_failure,display_failure', [(None, None), ('open', None),
    ('read', None), ('invalid', None), ('release', None), (None, 'open'),
    (None, 'render'), (None, 'show'), (None, 'poll'), (None, 'close'), (None, 'interrupt')])
def test_all_exit_paths_cleanup(camera_failure, display_failure):
    camera, display = FakeCamera(camera_failure), FakeDisplay(display_failure)
    app = Application(camera, display, MotionDetector(Config()), AlertState(0.5))
    if camera_failure or display_failure:
        with pytest.raises((RuntimeError, ValueError, KeyboardInterrupt)):
            app.run()
    else:
        app.run()
        assert display.alerts == [False]
    assert camera.released and display.closed


def test_original_failure_survives_cleanup_failure():
    camera, display = FakeCamera('release'), FakeDisplay('show')
    with pytest.raises(RuntimeError, match='show failed'):
        Application(camera, display, MotionDetector(Config()), AlertState(0.5)).run()
    assert camera.released and display.closed


def test_detector_failure_cleanup(monkeypatch):
    camera, display = FakeCamera(), FakeDisplay()
    detector = MotionDetector(Config())
    def fail(frame):
        raise RuntimeError('detector failed')
    monkeypatch.setattr(detector, 'process', fail)
    with pytest.raises(RuntimeError, match='detector failed'):
        Application(camera, display, detector, AlertState(0.5)).run()
    assert camera.released and display.closed


def test_full_sequence_hold_without_stale_boxes():
    frames = [np.zeros((120, 160, 3), np.uint8) for _ in range(4)]
    for item in frames[1:]:
        item[30:70, 40:90] = 255
    class SequenceCamera(FakeCamera):
        def read(self):
            self.reads += 1
            return frames[self.reads - 1]
    class SequenceDisplay(FakeDisplay):
        def __init__(self):
            super().__init__()
            self.boxes = []
        def render(self, frame, alert, boxes):
            self.boxes.append(boxes)
            return super().render(frame, alert, boxes)
        def poll_quit(self):
            return len(self.alerts) == 4
    times = iter([0.0, 0.25, 0.5])
    camera, display = SequenceCamera(), SequenceDisplay()
    Application(camera, display, MotionDetector(Config()), AlertState(0.5, lambda: next(times))).run()
    assert display.alerts == [False, True, True, False]
    assert display.boxes[1] and display.boxes[2:] == [[], []]
    assert camera.released and display.closed


def test_subsequent_read_failure():
    class LaterFailure(FakeCamera):
        def read(self):
            if self.reads:
                raise RuntimeError('later read failed')
            return super().read()
    camera, display = LaterFailure(), FakeDisplay()
    display.poll_quit = lambda: False
    with pytest.raises(RuntimeError, match='later read failed'):
        Application(camera, display, MotionDetector(Config()), AlertState(0.5)).run()
    assert camera.released and display.closed

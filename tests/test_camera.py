import cv2
import numpy as np
import pytest
from motion_app.camera import Camera, CameraError
from motion_app.preprocessing import FrameError


class Capture:
    def __init__(self, opened=True, success=True, frame=None):
        self.opened, self.success = opened, success
        self.frame = np.zeros((40, 50, 3), np.uint8) if frame is None else frame
        self.releases = 0
    def open(self, index): return self.opened
    def isOpened(self): return self.opened
    def read(self): return self.success, self.frame
    def release(self): self.releases += 1


@pytest.mark.parametrize('opened,success,invalid', [(True, True, False),
    (False, True, False), (True, False, False), (True, True, True)])
def test_camera_boundary_and_idempotent_release(monkeypatch, opened, success, invalid):
    capture = Capture(opened, success)
    if invalid: capture.frame = np.zeros((0, 0, 3), np.uint8)
    monkeypatch.setattr(cv2, 'VideoCapture', lambda: capture)
    camera = Camera(0)
    try:
        if not opened:
            with pytest.raises(CameraError): camera.open()
        else:
            camera.open()
            if not success or invalid:
                with pytest.raises((CameraError, FrameError)): camera.read()
            else:
                assert camera.read().shape == (40, 50, 3)
    finally:
        camera.release()
        camera.release()
    assert capture.releases == 1

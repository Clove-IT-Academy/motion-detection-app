import numpy as np
import pytest
from motion_app.config import Config
from motion_app.motion_detector import MotionDetector


def frame():
    return np.zeros((120, 160, 3), np.uint8)


def test_first_quiet_movement_stopped_and_reset():
    detector = MotionDetector(Config())
    quiet = frame()
    assert detector.process(quiet).baseline_reset
    assert not detector.process(quiet).motion
    changed = quiet.copy()
    changed[30:70, 40:90] = 255
    result = detector.process(changed)
    assert result.motion and len(result.boxes) == 1
    x, y, w, h = result.boxes[0]
    assert x <= 40 and y <= 30 and x + w >= 90 and y + h >= 70
    assert not detector.process(changed).motion
    assert detector.process(np.zeros((50, 50, 3), np.uint8)).baseline_reset
    detector.reset()
    assert detector.process(quiet).baseline_reset


def test_noise_filtered_and_multiple_regions():
    detector = MotionDetector(Config())
    quiet = frame()
    detector.process(quiet)
    noisy = quiet.copy()
    noisy[10, 10] = 255
    assert not detector.process(noisy).motion
    noisy[20:50, 20:50] = 255
    noisy[70:105, 110:145] = 255
    assert len(detector.process(noisy).boxes) == 2


@pytest.mark.parametrize('pixel,motion', [(25, False), (26, True)])
def test_threshold_strictly_greater(pixel, motion):
    detector = MotionDetector(Config(blur_kernel=1, morphology_kernel=1, min_area=1))
    quiet = frame()
    detector.process(quiet)
    changed = quiet.copy()
    changed[10:20, 10:20] = pixel
    assert detector.process(changed).motion == motion


@pytest.mark.parametrize('area,motion', [(81, True), (81.1, False)])
def test_contour_area_inclusive(area, motion):
    # A 10x10 filled pixel block has geometric contour area 9x9, not 100.
    detector = MotionDetector(Config(blur_kernel=1, morphology_kernel=1, min_area=area))
    quiet = frame()
    detector.process(quiet)
    changed = quiet.copy()
    changed[10:20, 10:20] = 255
    original = changed.copy()
    assert detector.process(changed).motion == motion
    np.testing.assert_array_equal(changed, original)

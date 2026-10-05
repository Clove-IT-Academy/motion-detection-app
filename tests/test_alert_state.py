from motion_app.app import AlertState
from motion_app.motion_detector import DetectionResult


def test_hold_refresh_expiry_and_reset():
    now = [1.0]
    state = AlertState(0.5, lambda: now[0])
    quiet = DetectionResult(False, [])
    motion = DetectionResult(True, [(0, 0, 1, 1)])
    assert not state.update(quiet)
    assert state.update(motion)
    now[0] = 1.25
    assert state.update(quiet)
    assert state.update(motion)
    now[0] = 1.75
    assert not state.update(quiet)
    assert state.update(motion)
    assert not state.update(DetectionResult(False, [], True))
    assert not state.update(quiet)


def test_zero_hold():
    state = AlertState(0, lambda: 1.0)
    assert state.update(DetectionResult(True, []))
    assert not state.update(DetectionResult(False, []))

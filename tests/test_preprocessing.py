import numpy as np
import pytest
from motion_app.preprocessing import FrameError, prepare_frame, validate_frame


@pytest.mark.parametrize('frame', [None, [], np.zeros((0, 2, 3), np.uint8),
    np.zeros((2, 2), np.uint8), np.zeros((2, 2, 4), np.uint8),
    np.zeros((2, 2, 3), np.float32), np.zeros((8193, 1, 3), np.uint8)])
def test_invalid_frames(frame):
    with pytest.raises(FrameError):
        validate_frame(frame)


def test_preparation_preserves_source():
    frame = np.full((40, 50, 3), 100, np.uint8)
    original = frame.copy()
    prepared = prepare_frame(frame, 5)
    assert prepared.shape == (40, 50)
    np.testing.assert_array_equal(frame, original)

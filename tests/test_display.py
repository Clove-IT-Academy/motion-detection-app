import cv2
import numpy as np
import pytest
from motion_app.display import Display, DisplayError


@pytest.mark.parametrize('shape', [(480, 640, 3), (60, 100, 3), (1, 1, 3)])
@pytest.mark.parametrize('show_boxes', [True, False])
def test_render_preserves_source(shape, show_boxes):
    frame = np.full(shape, 100, np.uint8)
    original = frame.copy()
    result = Display(show_boxes).render(frame, True, [(0, 0, 1, 1)])
    assert result.shape == frame.shape
    assert not np.shares_memory(result, frame)
    np.testing.assert_array_equal(frame, original)


@pytest.mark.parametrize('key', [ord('q'), ord('Q'), 27])
def test_quit_key(monkeypatch, key):
    monkeypatch.setattr(cv2, 'waitKey', lambda _: key)
    assert Display(True).poll_quit()


def test_native_close_no_recreation(monkeypatch):
    display = Display(True)
    monkeypatch.setattr(cv2, 'waitKey', lambda _: -1)
    monkeypatch.setattr(cv2, 'getWindowProperty', lambda *args: 0)
    assert display.poll_quit()
    with pytest.raises(DisplayError):
        display.show(np.zeros((5, 5, 3), np.uint8))


@pytest.mark.parametrize('backend', ['', 'WAYLAND'])
def test_unsupported_backend(monkeypatch, backend):
    monkeypatch.setattr(cv2, 'currentUIFramework', lambda: backend)
    with pytest.raises(DisplayError):
        Display(True).open()


def test_destroyed_window_property_error_exits(monkeypatch):
    monkeypatch.setattr(cv2, 'waitKey', lambda _: -1)
    def destroyed(*args):
        raise cv2.error('window destroyed')
    monkeypatch.setattr(cv2, 'getWindowProperty', destroyed)
    assert Display(True).poll_quit()

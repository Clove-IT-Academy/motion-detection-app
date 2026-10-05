"""Own the capture handle and report safe, actionable device errors."""

import cv2

from .preprocessing import Frame, validate_frame


class CameraError(RuntimeError):
    """The camera could not be opened or read."""


class Camera:
    def __init__(self, index: int) -> None:
        self.index = index
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        if self._capture is not None:
            raise CameraError("Camera is already open.")
        # Assign before open so cleanup also covers partial initialization.
        self._capture = cv2.VideoCapture()
        if not self._capture.open(self.index) or not self._capture.isOpened():
            raise CameraError("Cannot open camera. Check --camera-index, camera permissions, and whether another app is using it.")

    def read(self) -> Frame:
        if self._capture is None:
            raise CameraError("Camera is not open.")
        success, frame = self._capture.read()
        if not success:
            raise CameraError("Camera read failed. Check the connection and restart the app.")
        return validate_frame(frame)

    def release(self) -> None:
        capture, self._capture = self._capture, None
        if capture is not None:
            capture.release()

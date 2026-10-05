"""Application lifecycle and display-only alert persistence."""

import logging
from collections.abc import Callable
from time import monotonic
from typing import Protocol

from .motion_detector import DetectionResult, MotionDetector, Box
from .preprocessing import Frame, validate_frame

logger = logging.getLogger(__name__)


class FrameSource(Protocol):
    def open(self) -> None: ...
    def read(self) -> Frame: ...
    def release(self) -> None: ...


class Preview(Protocol):
    def open(self) -> None: ...
    def render(self, frame: Frame, alert: bool, boxes: list[Box]) -> Frame: ...
    def show(self, frame: Frame) -> None: ...
    def poll_quit(self) -> bool: ...
    def close(self) -> None: ...


class AlertState:
    def __init__(self, hold_seconds: float, clock: Callable[[], float] = monotonic) -> None:
        self.hold_seconds = hold_seconds
        self.clock = clock
        self._last_motion: float | None = None

    def update(self, result: DetectionResult) -> bool:
        if result.baseline_reset:
            self._last_motion = None
            return False
        now = self.clock()
        if result.motion:
            self._last_motion = now
            return True
        return self._last_motion is not None and now - self._last_motion < self.hold_seconds


class Application:
    def __init__(self, camera: FrameSource, display: Preview, detector: MotionDetector,
                 alert: AlertState) -> None:
        self.camera, self.display = camera, display
        self.detector, self.alert = detector, alert

    def run(self) -> None:
        failed = False
        try:
            self.camera.open()
            self.display.open()
            while True:
                frame = validate_frame(self.camera.read())
                result = self.detector.process(frame)
                image = self.display.render(frame, self.alert.update(result), result.boxes)
                self.display.show(image)
                # Poll immediately after show, before another imshow can recreate a closed window.
                if self.display.poll_quit():
                    break
        except BaseException:
            failed = True
            raise
        finally:
            cleanup_error: Exception | None = None
            # Try each resource independently and preserve any original exception.
            for cleanup in (self.camera.release, self.display.close):
                try:
                    cleanup()
                except Exception as error:
                    logger.error("Resource cleanup failed (%s).", type(error).__name__)
                    if cleanup_error is None:
                        cleanup_error = error
            if cleanup_error is not None and not failed:
                raise RuntimeError("Resource cleanup failed; restart the app before reusing the camera.") from cleanup_error

"""Consecutive-frame differencing; no camera, window, clock, or persistence."""

from dataclasses import dataclass

import cv2
import numpy as np

from .config import Config
from .preprocessing import Frame, prepare_frame

Box = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class DetectionResult:
    motion: bool
    boxes: list[Box]
    baseline_reset: bool = False


class MotionDetector:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._previous: Frame | None = None
        self._kernel = np.ones((config.morphology_kernel, config.morphology_kernel), np.uint8)

    def reset(self) -> None:
        self._previous = None

    def process(self, frame: Frame) -> DetectionResult:
        current = prepare_frame(frame, self.config.blur_kernel)
        previous = self._previous
        # Always advance the baseline: a stationary object must eventually be quiet.
        self._previous = current
        if previous is None or previous.shape != current.shape:
            return DetectionResult(False, [], baseline_reset=True)
        difference = cv2.absdiff(previous, current)
        _, mask = cv2.threshold(difference, self.config.threshold, 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(contour) for contour in contours
                 if cv2.contourArea(contour) >= self.config.min_area]
        return DetectionResult(bool(boxes), boxes)

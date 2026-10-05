"""Validate the capture boundary and reduce sensor noise without mutating input."""

import cv2
import numpy as np
from numpy.typing import NDArray

Frame = NDArray[np.uint8]


class FrameError(ValueError):
    """A capture did not return a supported image."""


def validate_frame(frame: object) -> Frame:
    # Bound dimensions before native operations and avoid leaking pixels in errors.
    if (not isinstance(frame, np.ndarray) or frame.dtype != np.uint8
            or frame.ndim != 3 or frame.shape[2] != 3
            or not 1 <= frame.shape[0] <= 8192 or not 1 <= frame.shape[1] <= 8192
            or frame.shape[0] * frame.shape[1] > 33_554_432):
        raise FrameError("Camera returned an invalid frame; expected a nonempty uint8 BGR image (maximum 32 megapixels).")
    return frame


def prepare_frame(frame: Frame, blur_kernel: int) -> Frame:
    gray = cv2.cvtColor(validate_frame(frame), cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

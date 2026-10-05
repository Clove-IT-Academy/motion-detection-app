"""CLI boundary; help and configuration do not access a camera."""

import argparse
import logging
import sys
from collections.abc import Sequence

from . import __version__
from .config import Config


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local webcam motion detection; no video is saved or transmitted.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--threshold", type=int, default=25, help="Pixel difference must exceed this value (0-255).")
    parser.add_argument("--min-area", type=float, default=500, help="Minimum contour area in pixels (positive).")
    parser.add_argument("--hold-seconds", type=float, default=0.5)
    parser.add_argument("--boxes", action=argparse.BooleanOptionalAction, dest="show_boxes", default=True)
    args = parser.parse_args(argv)
    try:
        config = Config(**vars(args))
    except ValueError as error:
        parser.error(str(error))
    # Delay native-library imports until after help and configuration validation.
    from .app import AlertState, Application
    from .camera import Camera, CameraError
    from .display import Display, DisplayError
    from .motion_detector import MotionDetector
    from .preprocessing import FrameError
    import cv2

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        Application(Camera(config.camera_index), Display(config.show_boxes),
                    MotionDetector(config), AlertState(config.hold_seconds)).run()
    except KeyboardInterrupt:
        return 0
    except (CameraError, DisplayError, FrameError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except cv2.error:
        print("Error: OpenCV camera or display operation failed. Check camera permissions and the desktop GUI installation.", file=sys.stderr)
        return 1
    except Exception as error:
        # Exception strings from arbitrary libraries may embed input data.
        print(f"Error: Unexpected application failure ({type(error).__name__}); cleanup was attempted.", file=sys.stderr)
        return 1
    return 0

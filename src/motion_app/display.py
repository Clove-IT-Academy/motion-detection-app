"""Render on a copy and own native window/event handling."""

import cv2

from .motion_detector import Box
from .preprocessing import Frame


class DisplayError(RuntimeError):
    """Desktop display is unavailable or its event state cannot be read."""


class Display:
    def __init__(self, show_boxes: bool) -> None:
        self.show_boxes = show_boxes
        self.name = "Motion Detection"
        self._created = False
        self._closed = False

    def open(self) -> None:
        backend = cv2.currentUIFramework()
        if not backend or backend == "WAYLAND":
            # Wayland does not support getWindowProperty; don't promise native close.
            raise DisplayError("A desktop OpenCV GUI with window-close support is required. Use GUI-enabled opencv-python and an X11/Cocoa/Win32/Qt desktop session.")
        self._created = True
        cv2.namedWindow(self.name, cv2.WINDOW_AUTOSIZE)

    def render(self, frame: Frame, alert: bool, boxes: list[Box]) -> Frame:
        image = frame.copy()
        if self.show_boxes:
            for x, y, width, height in boxes:
                cv2.rectangle(image, (x, y), (x + width - 1, y + height - 1), (0, 255, 255), 2)
        # Fit two lines within the actual image; camera pixels are never resized.
        lines = ["Motion detected!" if alert else "No motion detected", "Quit: q / Esc / close window"]
        height, width = image.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = min(0.7, max(0.01, (width - 12) / 520), max(0.01, (height - 8) / 100))
        thickness = 1
        line_height = max(1, cv2.getTextSize(lines[1], font, scale, thickness)[0][1] + 6)
        cv2.rectangle(image, (0, 0), (width - 1, min(height - 1, line_height * 2 + 8)), (0, 0, 0), -1)
        for index, text in enumerate(lines):
            cv2.putText(image, text, (min(6, width - 1), min(height - 1, (index + 1) * line_height)),
                        font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
        return image

    def show(self, frame: Frame) -> None:
        if not self._created or self._closed:
            raise DisplayError("Preview window is closed.")
        cv2.imshow(self.name, frame)

    def poll_quit(self) -> bool:
        key = cv2.waitKey(1)
        if key >= 0 and key & 0xFF in (ord("q"), ord("Q"), 27):
            return True
        try:
            visible = cv2.getWindowProperty(self.name, cv2.WND_PROP_VISIBLE)
        except cv2.error:
            # Some backends throw once the native window has been destroyed.
            self._closed = True
            return True
        if visible < 1:
            self._closed = True
        return self._closed

    def close(self) -> None:
        if self._created:
            self._created = False
            self._closed = True
            cv2.destroyAllWindows()

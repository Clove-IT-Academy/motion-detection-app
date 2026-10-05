"""Validated settings, independent of devices and user interfaces."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class Config:
    camera_index: int = 0
    threshold: int = 25
    min_area: float = 500
    hold_seconds: float = 0.5
    show_boxes: bool = True
    blur_kernel: int = 5
    morphology_kernel: int = 3

    def __post_init__(self) -> None:
        for name, low, high in (("camera_index", 0, None), ("threshold", 0, 255),
                                ("blur_kernel", 1, 31), ("morphology_kernel", 1, 31)):
            value = getattr(self, name)
            if type(value) is not int or value < low or (high is not None and value > high):
                raise ValueError(f"{name} must be an integer in the range {low}..{high or 'unbounded'}.")
        for name in ("blur_kernel", "morphology_kernel"):
            if getattr(self, name) % 2 == 0:
                raise ValueError(f"{name} must be odd.")
        for name, positive in (("min_area", True), ("hold_seconds", False)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{name} must be a finite number.")
            if value < 0 or (positive and value == 0):
                raise ValueError(f"{name} must be {'positive' if positive else 'nonnegative'}.")
        if type(self.show_boxes) is not bool:
            raise ValueError("show_boxes must be a boolean.")

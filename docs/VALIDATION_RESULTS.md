# Validation results

Date: 2026-10-05. Implementation candidate: 0.1.0.
Environment: macOS 27.0 arm64, Python 3.14.7, OpenCV Python distribution
5.0.0.93 (cv2 reports 5.0.0), NumPy 2.5.3, pytest 9.1.1, Cocoa GUI.

## Completed checks

- Installed latest stable compatible packages using project `venv/bin/python -m pip`;
  pinned all resolved development dependencies in `requirements-dev.txt`.
- Editable installation and CLI help/version succeed without device access.
- 66 camera-free tests pass, with Python warnings treated as errors. Coverage
  includes configuration, frame validation, first/reset frames, identical/noisy/
  changed/stopped scenes, multiple contours, strict threshold and inclusive area,
  fake-clock hold refresh/expiry, current boxes during held alert, quit keys,
  native-close simulation, partial startup, subsequent read failure, exceptions,
  independent cleanup, and source preservation.
- Fresh temporary venv installation from the pinned requirements succeeds;
  editable app installation and the same test suite succeed there.
- `pip check`, bytecode compilation, and whitespace diff checks pass.
- Native synthetic-image preview opens, polls events, and closes on Cocoa.
- Synthetic 640x480 detector benchmark: 300 alternating-block frames averaged
  0.217 ms per detector call on this machine. This excludes camera capture and
  display and is not a live-camera FPS or usability claim.
- Source review: no image/media writer, network client, analytics, or frame logs.
  Only the previous prepared frame is retained between calls; no frame history.

## Live camera result and remaining limits

A bounded camera-index-0 smoke run was attempted. OpenCV reported camera access
not authorized and failed to initialize. The camera adapter produced its
permission/index/device-contention error and cleanup ran. No frames were saved
or transmitted. Camera permission must be granted to the terminal/host app
before real-camera tests can continue.

The first synthetic GUI attempt inside the restricted execution environment
aborted; repeating the native GUI smoke outside that restriction succeeded.
Native GUI operation therefore needs a normal desktop launch context.

Manual movement/noise calibration, live responsiveness, native window-close
interaction, camera reuse after each exit path, extended camera runs, and
another-student handoff remain unverified. Windows/Linux are unverified. No
full release acceptance or universal platform support is claimed.

## Requirement evidence

| Requirement | Current state |
| --- | --- |
| R1 preview | Synthetic native preview passed; webcam blocked by permission |
| R2 detection | Synthetic sequence and boundary tests passed; live calibration pending |
| R3 status/timing | Fake-clock and integration tests passed; live flicker check pending |
| R4 overlay | Copy/layout/current-box tests passed; live readability pending |
| R5 quit | Key/window simulations and native programmatic cleanup passed; manual controls pending |
| R6 failures | Capture, invalid-read, component-failure and cleanup tests passed; device-disconnect check pending |
| R7 privacy | Source review passed; extended live run pending |
| R8 boundaries | Separate modules and camera-free tests implemented |
| R9 reproducibility | Fresh venv installation passed; another-student handoff pending |
| R10 responsiveness | Synthetic detector timing recorded; live loop measurement pending |

## API and release references

Release checks: [OpenCV Python](https://pypi.org/project/opencv-python/),
[NumPy](https://pypi.org/project/numpy/), [pytest](https://pypi.org/project/pytest/).
API review: [OpenCV HighGUI](https://docs.opencv.org/4.x/d7/dfc/group__highgui.html)
and [contours](https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html).
Used installed public APIs: currentUIFramework, namedWindow, imshow, waitKey,
getWindowProperty, destroyAllWindows, VideoCapture, cvtColor, GaussianBlur,
absdiff, threshold, morphologyEx, findContours, contourArea, and boundingRect.
No Python deprecation warning was emitted in the tested paths. Native GUI APIs
still have backend-specific constraints; Wayland is rejected explicitly because
window-property inspection is unsupported there.

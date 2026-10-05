# Motion Detection App

A local Python/OpenCV webcam app that compares consecutive frames and displays
`Motion detected!` or `No motion detected`. Optional boxes show current changed
regions. Frames stay in memory: no recording, screenshots, uploads, or analytics.

## Setup with a virtual environment

Python 3.14 is required; development was tested with Python 3.14.7 on macOS arm64.
Native webcam permissions and window behavior still require the manual checks in
[docs/MANUAL_TEST_CHECKLIST.md](docs/MANUAL_TEST_CHECKLIST.md). Windows/Linux are unverified.

From this project directory:

```sh
python3.14 -m venv venv  # skip if the project venv already exists
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python -m pip install --no-build-isolation --no-deps -e .
venv/bin/python -m motion_app
```

On Windows, use `venv\Scripts\python.exe` in place of `venv/bin/python`.
The pinned GUI OpenCV wheel requires a compatible desktop OS/wheel (on this
machine, macOS 14 or later for NumPy). Install only `opencv-python`, not headless
or contrib variants alongside it. Internet access is needed for installation;
the application itself does not communicate over the network.

## Controls and sensitivity

Focus the preview window and press **q** or **Esc**, or close the window. Ctrl+C
also cleans up and exits. Configuration is selected at startup:

```sh
venv/bin/python -m motion_app --help
venv/bin/python -m motion_app --camera-index 0 --threshold 25 --min-area 500 --hold-seconds 0.5
venv/bin/python -m motion_app --threshold 15 --min-area 200 --no-boxes
```

- `--camera-index`: nonnegative device index; default 0.
- `--threshold`: difference must exceed this value, 0-255; default 25.
- `--min-area`: qualifying contour area must be at least this positive pixel area; default 500.
- `--hold-seconds`: nonnegative finite alert persistence after last movement; default 0.5. Zero disables persistence.
- `--boxes` / `--no-boxes`: show/hide current-frame boxes; default enabled.
- `--version`: print version without opening devices.

Lower thresholds/areas increase sensitivity and false alerts. Defaults are
starting points, not calibrated universal settings. Capture resolution is left
to the camera; area thresholds depend on actual dimensions. Internal 5x5 blur
and 3x3 opening/closing remove small noise. The first frame and any dimension
change establish a new baseline without an alert. Stopped objects cease causing
raw detection after adjacent frames stabilize; the held message then expires.
Lighting changes and camera shake may alert. Very small/slow/low-contrast motion
may be missed. Boxes represent current motion, so a held message can have no boxes.

## Verification

```sh
venv/bin/python -m pytest
venv/bin/python -m pip check
```

Tests use synthetic arrays, fake capture/window adapters, and fake clocks; they
never open your webcam. See [validation results](docs/VALIDATION_RESULTS.md) for
checks actually performed and [release checklist](docs/RELEASE_CHECKLIST.md) for
remaining handoff gates. Version 0.1.0 is an implementation candidate, pending
real-camera calibration and acceptance. No fixed webcam FPS is promised.

## Troubleshooting

If opening fails, check the device index, connection, camera permission for the
terminal/host app, and whether another app owns the device. On macOS check
System Settings > Privacy & Security > Camera. Restart after a disconnected
camera: v1 stops on failed reads rather than retrying stale frames.

GUI errors require a desktop session and GUI-enabled OpenCV. Wayland is rejected
because OpenCV window-property inspection does not support its native-close
contract; use an X11 session. Tiny camera frames can make overlays unreadable.
A camera backend can block during capture; quit responsiveness needs hardware
validation. No frames are written for diagnostics.

Exit status: 0 for quit/Ctrl+C, 1 for runtime or cleanup failure, 2 for invalid
arguments/configuration. Reports should include app/Python/library versions,
OS, camera model if known, settings, reproduction steps, and error text. Do not
include personal footage. Maintenance owner: not yet assigned.

## Structure

`camera.py` owns capture; `preprocessing.py` validates/prepares images;
`motion_detector.py` compares frames; `display.py` draws and polls events;
`app.py` owns lifecycle and alert timing; `config.py` validates defaults;
`main.py` handles the CLI. Comments explain baseline, copying, native-window,
and cleanup decisions. See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) and the
architecture PDF for scope and future work.

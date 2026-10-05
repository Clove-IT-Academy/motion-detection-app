# Motion Detection with Python and OpenCV
## Theory, Code Walkthrough, and a Bridge to Object Detection

**Author: Shashank Jha**  
Audience: students with basic Python knowledge who are beginning computer vision.  
Edition: 1.0, 2026-10-05.  
Application snapshot: motion-detection-app, version 0.1.0.

---

## Instructions for generating the student PDF

This file is a self-contained manuscript and source-code snapshot. Upload it to ChatGPT web UI and use the following prompt. The instructions in this section are for producing the PDF; omit this section from the student-facing notes.

> Create complete, beginner-friendly PDF course notes from this Markdown file. Use the title “Motion Detection with Python and OpenCV: Theory, Code Walkthrough, and a Bridge to Object Detection” and credit **Shashank Jha** as the author on the cover. Use the attached manuscript and embedded source as the factual baseline. Explain concepts before the code that uses them. Preserve the distinction between this implemented motion-detection app and the future object-detection learning path. Include a cover, table of contents, learning objectives, numbered chapters, labeled pipeline and lifecycle diagrams, worked calculations, readable code listings, module-by-module explanations, glossary, exercises, and answer guidance. Explain every nontrivial source-code construct and algorithmic step; do not merely repeat code. Keep code and equations legible, wrap long lines without changing Python semantics, avoid splitting short examples across pages, and use page numbers and consistent typography. The full source appendix must match the snapshot rather than an invented rewrite. Label simplified examples, conceptual pseudocode, and future extensions clearly. Preserve the reported validation limits; do not claim live-camera acceptance, universal support, or measured webcam FPS. Do not invent model names, library versions, installation commands, training results, or functionality. If expanding the future object-detection section with a runnable framework example, verify current official documentation and compatibility first, cite the source, and place it in a separate environment; otherwise retain the framework-neutral learning path. Use PDF creation/rendering tools or skills if they are available in this session, inspect the rendered pages, and provide a downloadable PDF. If PDF generation is unavailable, provide the formatted notes and explain that limitation accurately. Do not include this production prompt in the final notes.

Editorial guidance: retain the full educational coverage. Prefer a sufficient page count over shrinking type or omitting explanation. Draw clean diagrams rather than printing unresolved Mermaid syntax. Use synthetic illustrations rather than identifiable webcam photos. A PDF generator does not need webcam access to explain this app.

---

# Part I - Understanding the project

## 1. Learning objectives and prerequisites

After completing these notes, students should be able to:

1. Explain how a digital image becomes a NumPy array and how video becomes a sequence of frames.
2. Distinguish motion detection, image classification, object detection, and tracking.
3. Trace grayscale conversion, blur, frame differencing, thresholding, morphology, contours, and bounding boxes.
4. Explain baseline state and why stopped objects stop triggering this detector.
5. Understand alert persistence, monotonic clocks, frame copying, and resource cleanup.
6. Install and run the app in a virtual environment and adjust its sensitivity.
7. Test image-processing code with synthetic data and application flow with fake components.
8. Plan a separate first object-detection experiment without mistaking changed regions for recognized objects.

Prerequisites: Python variables, functions, loops, conditionals, lists, tuples, classes, imports, and basic exception handling. NumPy arrays and type annotations are explained below. No neural-network training or GPU is required for this motion app.

Suggested learning sequence: read Parts I-II, run the camera-free example, install the app, trace the module walkthrough alongside the appendix, complete the labs, then study the object-detection bridge.

## 2. What the app does

The app opens one webcam and displays its live image with a status message. It compares each prepared image with the preceding prepared image. If sufficiently large changed regions remain after noise filtering, it reports motion. Optional rectangles outline those current changed regions.

It runs locally in one process, keeps images in memory, and has no model download, training stage, recording, screenshot feature, upload, account system, or database. “All movement” means sufficiently visible frame-to-frame changes under the chosen settings, not a guarantee that every physical movement is detected.

Example: waving a hand changes many pixels, so a region may qualify. Holding the hand still eventually produces nearly identical adjacent frames, so raw motion ends. A light switching on may also change many pixels even though no object moved.

### Motion detection is not object detection

| Task | Question | Typical result | Implemented here? |
| --- | --- | --- | --- |
| Motion detection | Which parts changed between frames? | Motion flag and changed-region boxes | Yes |
| Image classification | What category describes this image? | Image-level label/score | No |
| Object detection | Which known objects are present, and where? | Class, score, and box per prediction | No |
| Segmentation | Which pixels belong to a region/category/instance? | Pixel-level masks | No learned segmentation; only a binary change mask |
| Tracking | Which detections correspond to the same entity over time? | Associated trajectories/track IDs | No |

A rectangle is a geometric representation, not proof of recognition. One moving object can generate several changed regions; several objects can merge into one region. This app produces no person/car/animal labels and no classification confidence scores.

## 3. Architecture and data flow

```text
Webcam -> Camera.read -> Frame validation
       -> Grayscale + Gaussian blur
       -> Previous/current difference -> Binary threshold
       -> Opening + closing -> Contours -> Area filtering
       -> DetectionResult -> AlertState -> Overlay copy -> Preview
                                                    -> Quit events

Application owns startup, coordination, and guaranteed cleanup.
```

`camera.py` handles hardware, `preprocessing.py` prepares images, `motion_detector.py` owns comparison state, `app.py` owns alert timing/lifecycle, `display.py` owns drawing/events, `config.py` validates settings, and `main.py` handles command-line entry and user errors.

Keeping these responsibilities separate lets students test detection without a camera and test cleanup without a desktop window. A camera failure is different from a wrong algorithm result; the design keeps those investigations separate.

# Part II - Image-processing theory

## 4. Images, arrays, coordinates, and unsigned arithmetic

A color frame is a NumPy array with shape `(height, width, channels)`. This app expects three BGR channels and dtype `uint8`. Each channel holds an integer from 0 to 255. OpenCV commonly uses blue, green, red ordering for camera images; many other image/model interfaces use RGB. Always check the interface before converting.

Array indexing is `frame[y, x]`: rows first, columns second. A box is `(x, y, width, height)`. For a 640x480 image, `frame.shape` is `(480, 640, 3)`, not `(640, 480, 3)`. Memory for the raw pixels is approximately `480 * 640 * 3 = 921,600` bytes; temporary arrays add further memory.

A slice such as `frame[30:70, 40:90] = 255` fills rows 30-69 and columns 40-89 in all channels with white. Slice endpoints are exclusive. NumPy enables whole-array operations rather than writing a slow Python loop over every pixel.

Unsigned subtraction can wrap: in 8-bit arithmetic, directly subtracting 100 from 20 does not safely produce a signed -80. `cv2.absdiff` computes the intended absolute difference for supported arrays. Do not replace it with naive `np.abs(a - b)` on uint8 data without considering dtype conversion.

## 5. Grayscale conversion

A grayscale image has one intensity value per pixel. For common BGR-to-gray conversion, a useful approximate formula is:

\[
G = 0.114B + 0.587G_{channel} + 0.299R.
\]

The channel subscript prevents confusing the green channel with grayscale output. These weights are not a simple equal-channel average. OpenCV handles the actual integer conversion and rounding.

Example: a pure red BGR pixel `(0, 0, 255)` becomes approximately 76. Grayscale reduces three channels to one for simpler comparison and less per-frame work. It also discards color information: changes with similar grayscale intensity can become less visible.

Code: `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)`.

## 6. Gaussian blur and kernels

Sensor noise can change isolated pixels even in a quiet scene. Gaussian blur replaces each pixel with a weighted neighborhood average, giving nearby pixels more influence. A kernel is the neighborhood/filter used for this operation.

Conceptually:

\[
S(x,y) = \sum_{i,j} K(i,j) I(x-i,y-j), \qquad \sum_{i,j}K(i,j)=1.
\]

The app uses a 5x5 Gaussian kernel and sigma 0, letting OpenCV derive sigma from the kernel size. Odd dimensions give a central pixel. Blurring suppresses small fluctuations but can also weaken tiny movement and soften edges. It is a sensitivity tradeoff, not a universally beneficial improvement.

Code: `cv2.GaussianBlur(gray, (5, 5), 0)`.

The app allows positive odd internal kernel dimensions up to 31 through `Config`, but does not expose them as command-line controls.

## 7. Consecutive-frame differencing and baseline state

Let `P_t` be the current prepared grayscale frame. The detector computes:

\[
D_t(x,y) = |P_t(x,y)-P_{t-1}(x,y)|.
\]

If a pixel changes from 20 to 100, the difference is 80. If it changes from 100 to 20, the difference is also 80. Direction of brightness change does not matter.

The first frame has no predecessor. It becomes the baseline and returns no motion. Every valid processed frame replaces the baseline, including quiet frames. If dimensions change, comparison is unsafe: the app establishes a fresh baseline and clears held-alert state.

A moving block can create change at both its old and new locations. Boxes outline differences, not necessarily the complete current object. Small movement between high-rate adjacent frames can be weaker than movement observed over a larger interval; frame rate affects sensitivity.

## 8. Binary thresholding

With threshold `T`, the binary mask is:

\[
M_t(x,y)=\begin{cases}255 & D_t(x,y)>T\\0 & D_t(x,y)\leq T.\end{cases}
\]

Default `T = 25`. A difference of exactly 25 is quiet; a difference of 26 is changed. White represents changed pixels and black represents unchanged pixels. This is a change mask, not a learned object mask.

Lower threshold: more sensitivity and more noise alerts. Higher threshold: fewer weak changes, but possible missed motion. Threshold 255 means no uint8 difference can exceed it, so no motion qualifies. Threshold 0 reacts to any surviving nonzero difference.

## 9. Morphological opening and closing

Morphology changes shapes in a binary mask using a structuring element. Here the element is a 3x3 array of ones.

- **Erosion** shrinks white regions: a foreground pixel survives only when its neighborhood meets the kernel condition.
- **Dilation** expands white regions.
- **Opening**, erosion followed by dilation, removes small isolated foreground regions.
- **Closing**, dilation followed by erosion, fills small holes/gaps and can connect nearby foreground regions.

The app applies opening, then closing, with one iteration each. Illustrate these on small black/white grids in the PDF. Explain that stronger morphology can remove legitimate tiny changes or merge neighboring changes. Contour-area filtering happens after this cleanup, so original changed-pixel count is not the final region area.

## 10. Contours, area, and bounding rectangles

A contour describes a boundary around a binary region. `RETR_EXTERNAL` retrieves outer contours and does not separately return every nested hole. `CHAIN_APPROX_SIMPLE` compresses straight boundary segments to reduce stored points.

For each contour, the app checks `cv2.contourArea(contour) >= min_area`. Default area is 500 pixel-coordinate units. This is geometric contour area, not the number of white mask pixels and not bounding-box area.

Worked boundary example: a filled 10x10 block at integer pixel positions commonly has outer corner coordinates spanning 9 units per axis. Its contour area is 81, while its bounding rectangle is 10x10 and its foreground count is 100. The tests isolate this example with blur and morphology kernels of size 1.

`cv2.boundingRect(contour)` returns `(x, y, width, height)`. A result `(40, 30, 50, 40)` covers array rows `30:70` and columns `40:90`. Drawing through `x + width - 1` and `y + height - 1` matches inclusive pixel endpoints.

Larger capture resolution changes pixel areas. A region that spans 500 pixels at one resolution may span a different area at another. Always record actual dimensions when tuning; this app does not silently resize captures.

## 11. Raw detection versus alert persistence

The detector returns a raw motion flag for the current pair of frames. The UI separately keeps the message visible briefly to reduce flicker.

If qualifying movement last occurred at time `t_last`, with hold duration `H`:

\[
\text{held alert} = (t-t_{last}) < H.
\]

New motion always shows an alert immediately and refreshes `t_last`. With no new motion, the message persists only until this boundary. At exactly the expiry time it becomes quiet. Hold duration zero shows motion on a detected frame but adds no persistence afterward.

Example with H=0.5 seconds: motion at 1.0; quiet at 1.25 still shows the message; quiet at 1.5 clears it. Another motion at 1.3 refreshes expiry to 1.8.

A monotonic clock measures elapsed time without jumping when the system wall clock is adjusted. A fake clock lets tests check exact boundaries without sleeping. Current boxes are never retained merely because the message is held.

## 12. Cost, memory, and limitations

With fixed small kernels, image preparation, differencing, thresholding, and mask operations perform work proportional to image pixels, roughly O(height * width). Contour processing depends on mask complexity. Several current arrays and one previous prepared image use O(height * width) memory; memory must not grow with the number of processed frames.

Avoid claiming FPS from detector-only timing. Camera capture, buffering, preprocessing, display, and event polling all affect end-to-end latency. Native device reads may block. Smaller images can reduce computation but alter sensitivity and detail; resizing is not implemented here.

Common failure modes: noise, camera vibration, exposure/lighting changes, shadows, low contrast, slow/tiny motion, changed frame dimensions, camera permission, disconnected devices, and GUI-backend differences. General visible change is not a reliable semantic answer to “a person is present.”

# Part III - Installing and understanding the code

## 13. Virtual-environment setup and first run

A virtual environment isolates this project's Python packages from other projects. Run installation, scripts, and tests through its interpreter. Activation is optional when using the explicit interpreter path.

From the `motion-detection-app` directory:

```sh
python3.14 -m venv venv  # only if the project environment does not already exist
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python -m pip install --no-build-isolation --no-deps -e .
venv/bin/python -m motion_app --help
venv/bin/python -m motion_app
venv/bin/python -m pytest -q
venv/bin/python -m pip check
```

Creating the environment uses the installed base Python because the venv does not yet exist. All subsequent Python commands use the venv. On Windows replace `venv/bin/python` with `venv\Scripts\python.exe`; creating the environment may use `py -3.14 -m venv venv`. Windows compatibility has not been manually validated for this app.

`python -m pip` binds pip to the selected interpreter. `-e .` is an editable install: imports point to the source tree. `--no-build-isolation` uses the build tools already installed by the pinned requirements; `--no-deps` avoids resolving a different dependency set during app installation. Do not use these flags without first installing the requirements.

The snapshot was checked with Python 3.14.7, GUI OpenCV Python 5.0.0.93, NumPy 2.5.3, and pytest 9.1.1. These are the recorded versions for this edition, not a promise that they will remain the newest releases. See the dependency listings in the appendix. Compatible wheels/desktop environment are required.

Do not install headless OpenCV for this GUI app or mix competing OpenCV distributions in one environment. Internet is needed for package installation; app execution has no network feature.

## 14. Camera-free first experiment

After installing the package, create a local `synthetic_demo.py` containing this teaching example and run `venv/bin/python synthetic_demo.py`. It creates arrays in memory and does not open a camera or save images.

```python
import numpy as np
from motion_app.config import Config
from motion_app.motion_detector import MotionDetector

quiet = np.zeros((120, 160, 3), dtype=np.uint8)
changed = quiet.copy()
changed[30:70, 40:90] = 255

detector = MotionDetector(Config())
for name, frame in [("baseline", quiet), ("quiet", quiet),
                    ("changed", changed), ("stopped", changed)]:
    result = detector.process(frame)
    print(name, result.motion, result.baseline_reset, len(result.boxes))
```

Expected printed fields:

```text
baseline False True 0
quiet False False 0
changed True False 1
stopped False False 0
```

Explain every statement: creation, uint8 dtype, copy, slice, default configuration, stateful instance, tuple unpacking, iteration, process call, and result attributes. The duplicate changed frame models an object that has stopped. Exact box edges after blur can extend beyond the original block.

## 15. Configuration and command-line controls

```sh
venv/bin/python -m motion_app --camera-index 0 --threshold 25 --min-area 500 --hold-seconds 0.5
venv/bin/python -m motion_app --threshold 15 --min-area 200 --no-boxes
```

| Setting | Default | Meaning/constraint |
| --- | --- | --- |
| camera_index | 0 | Nonnegative integer device index |
| threshold | 25 | Integer 0-255, strict difference boundary |
| min_area | 500 | Finite positive contour area |
| hold_seconds | 0.5 | Finite nonnegative elapsed time |
| show_boxes | true | Boolean, controlled by --boxes/--no-boxes |
| blur_kernel | 5 | Internal odd positive integer <=31 |
| morphology_kernel | 3 | Internal odd positive integer <=31 |

The last two settings are configured in Python, not exposed as CLI flags. Defaults need environment-specific calibration. Focus the preview and press q, Q, or Esc; native close should exit too. Ctrl+C triggers cleanup. Exit codes are 0 for user shutdown, 1 for runtime/cleanup failure, and 2 for invalid CLI/configuration.

## 16. Python constructs used in the project

- **Dataclass:** generates common data-container methods such as initialization. `frozen=True` prevents field reassignment; `slots=True` avoids arbitrary instance attributes. A frozen result still contains a mutable list of boxes, so it is not deeply immutable.
- **`__post_init__`:** runs after generated initialization and rejects invalid settings immediately.
- **Type hints:** document contracts such as `Frame | None` and `list[Box]`; they do not automatically validate runtime values.
- **`Protocol`:** describes operations an adapter must support without requiring inheritance. Fake camera/display objects can satisfy these contracts in tests.
- **Dependency injection:** passes collaborators (camera, display, detector, clock) into classes so they can be replaced independently.
- **`Callable[[], float]`:** a no-argument function returning a time value. `lambda` supplies a short fake-clock function in tests.
- **Properties of Python booleans:** `bool` behaves as a subclass of `int`, so validators explicitly reject it where a genuine numeric setting is required.
- **Short-circuit boolean evaluation:** earlier checks prevent unsafe access to array dimensions on unsupported objects.
- **List comprehension:** builds boxes only from contours that meet the area condition.
- **Tuple unpacking/multiple assignment:** separates library results and detaches handles before cleanup.
- **`try/except/finally`:** separates ordinary operation, errors, and cleanup that must be attempted regardless of outcome.
- **`raise ... from error`:** preserves exception causality. Safe public messages avoid arbitrary data-containing error strings.
- **`__main__.py`:** enables `python -m motion_app`; `SystemExit` carries the integer exit status.
- **Private-name convention:** a leading underscore marks internal state such as `_previous`; it is a convention, not enforced secrecy.

## 17. Module-by-module source walkthrough

The complete source is in the appendix. Explain the following sections against those exact listings.

### `config.py`: fail before hardware access

`Config` centralizes defaults and checks integer types/ranges, odd kernels, finite numbers, and a true Boolean boxes flag. NaN and infinity must not pass time/area validation. Frozen configuration prevents accidental mid-run changes. Configuration knows nothing about OpenCV windows or camera readiness.

### `preprocessing.py`: boundary validation and pure preparation

`validate_frame` verifies ndarray, uint8, three-dimensional BGR layout, nonempty dimensions, and bounded size before native image operations. The maximum per-axis size is 8192 and maximum pixel count is 33,554,432. These are implementation safety limits, not claims about tested camera resolutions. Its error contains no pixels.

`prepare_frame` creates grayscale/blurred outputs without modifying the input. It relies on the validated `Config` contract for kernel size. The camera and controller both validate inputs: the controller's check also protects it when a replacement/fake source is used.

### `camera.py`: capture ownership

`open` stores a capture handle before trying to open the selected index, allowing cleanup after partial initialization. `read` checks success before validating or returning data. Failed reads stop the application rather than process the last good frame. `release` detaches its handle before releasing, making repeated cleanup safe. Releasing is attempted; a native cleanup failure is reported rather than proof that hardware has definitely released.

### `motion_detector.py`: stateful algorithm, structured output

The constructor stores settings, starts with no baseline, and creates the morphology kernel once. `process` prepares the current frame, retrieves the old baseline, and assigns the new prepared frame as the next baseline. First/shape-changed frames return `baseline_reset=True` and empty boxes. Normal frames follow the full pipeline described in Part II. `bool(boxes)` turns a nonempty result into `motion=True`. `reset` drops baseline state.

`DetectionResult` separates what happened from how it is displayed. Its `baseline_reset` default is False. No confidence or class label exists. Frame work is bounded; no frame history is retained.

### `app.py`: orchestration, clocks, and cleanup

`AlertState` owns `_last_motion`. Reset results clear it. Detected motion stores the current monotonic time. Quiet results compare elapsed time to hold duration. The controller validates, detects, updates alert state, renders, displays, and polls quit events in that order.

`finally` attempts camera and display cleanup independently. The `except BaseException` block is deliberately limited to marking the run as failed and immediately re-raising; it does not suppress interruption or other failures. If an original failure exists, cleanup errors must not replace it. If normal execution ends but cleanup fails, a runtime failure is raised. Only exception class names are logged for cleanup diagnostics.

### `display.py`: copying, accessibility, and native events

`render` starts with `frame.copy()`, draws current boxes when enabled, and adds white status text on a black panel. Drawing into detector inputs could create artificial motion from changing text; the copy prevents that feedback. Text scale uses actual dimensions; it does not resize camera pixels. Very tiny frames can remain unreadable despite avoiding crashes.

`waitKey(1)` services native GUI events as well as reading keys. It is not an exact one-millisecond frame timer or FPS limiter. The bit mask extracts a low-byte key code when a key is present. The code checks window visibility before another iteration can recreate a closed preview. A window-property error is treated as close because some backends throw after destruction; this is a backend assumption still requiring manual checks. Wayland is explicitly rejected because the needed property query is unsupported. Cleanup destroys app-owned OpenCV windows.

### `main.py`, `__main__.py`, and `__init__.py`: entering and exiting

`argparse` parses typed options, supports help/version, and provides both box flags through `BooleanOptionalAction`. `dest="show_boxes"` matches the dataclass field. `vars(args)` becomes keyword settings through `**`. Validation happens before camera/window construction. Native module imports are delayed so help and invalid-argument handling do not depend on device startup.

`main` assembles the app and translates known failures into safe error messages and exit codes. Unexpected error messages show the exception type rather than potentially sensitive arbitrary library text. `__init__.py` contains the version; `__main__.py` calls `main`.

# Part IV - Testing, labs, and debugging

## 18. What the tests demonstrate

Synthetic arrays establish controlled causes and expected outcomes. Fake adapters simulate startup/read/render/show/poll/cleanup failures; a fake clock tests exact expiry without waiting. Tests do not depend on personal footage or physical webcam access.

| Test area | Why it matters |
| --- | --- |
| First/identical frames | Avoid startup false alerts and quiet-scene defects |
| Large block/multiple regions | Check basic spatial change detection |
| Tiny noise | Check cleanup and area filtering |
| Threshold 25 vs 26 | Verify strict pixel boundary |
| Contour area 81 vs 81.1 | Verify inclusive area boundary |
| Repeated stable block | Verify stopped-object behavior |
| Frame shape reset | Avoid invalid comparisons and stale alerts |
| Alert exact expiry/refresh/zero hold | Prevent flicker/timing regressions |
| Held alert with empty current boxes | Prevent stale-region display |
| Invalid/missing capture | Stop unsafe native processing |
| Every failure path | Attempt release and window cleanup |
| Render input preservation | Prevent overlay feedback into detection |
| CLI help/configuration | Avoid accidental hardware access before validation |

Reported on 2026-10-05: 66 tests passed in project and fresh virtual environments; warnings were treated as errors. A native Cocoa preview using synthetic images passed. Live camera initialization was blocked by macOS camera permission. These notes do not assert that classroom movement/noise or native-close acceptance passed.

A detector-only synthetic benchmark averaged 0.217 ms for 300 alternating-block 640x480 frames on the development machine. Explain why this excludes capture/display and cannot establish webcam FPS. Results are a snapshot, not a universal performance guarantee.

## 19. Practical labs

### Lab A: inspect an array

Create a 120x160 BGR uint8 frame, print shape/dtype, fill a white block, and predict its row/column bounds before running. Do not save personal images.

### Lab B: tune one parameter at a time

Run the synthetic demo. Try pixel-change thresholds 25 and 255, then minimum areas above/below the region area. Record configuration, expected behavior, actual behavior, and explanation. Recreate the detector for independent trials because it retains a baseline.

### Lab C: isolate boundary behavior

Use blur/morphology kernels of 1. Make a 10x10 block with intensity 25, then 26. Test minimum area 81 and 81.1. Explain why white-pixel count, contour area, and box area differ.

### Lab D: test persistence without sleeping

Construct `AlertState(0.5, fake_clock)` and pass motion/quiet/reset results at selected times. Confirm alert expiry exactly at the boundary and clearing after reset. Track boxes independently from message timing.

### Lab E: explain cleanup

Read the fake-component tests. Simulate a read failure and a cleanup failure. Describe which exception remains primary and whether both resources were attempted. Never intentionally leave a real camera open to demonstrate failure.

### Lab F: optional real-camera calibration

After granting permission, use a stable camera and non-sensitive scene. Record dimensions/settings/lighting/distance. Test quiet, near/far movement, stopping, lighting changes, camera bump, all quit controls, and camera reuse. Do not save frames. This is required evidence for hardware acceptance, not something the synthetic tests can replace.

## 20. Troubleshooting and privacy

| Symptom | Likely checks |
| --- | --- |
| Package import fails | Correct project directory, venv interpreter, editable installation |
| Camera cannot open | Permission, index, cable, another app holding device |
| GUI failure | GUI OpenCV, desktop session, supported backend; no competing distributions |
| Constant alerts | Camera stability, lighting/exposure, threshold/area too sensitive |
| Missed movement | Region size/contrast, blur, high threshold/area, adjacent-frame changes |
| Alert persists briefly without boxes | Expected hold behavior; boxes are current only |
| Camera stops after disconnect | Expected fail-fast behavior; reconnect and restart |

Keep frames in memory. Operational messages can mention versions/settings/failure types, but should not contain pixels or identifiable footage. Package downloads during installation are distinct from transmitting camera content. An object-detection extension can introduce weights downloads or hosted inference; review that scope separately and do not assume it shares this app's network behavior.

# Part V - Getting started with object detection

## 21. From visible change to semantic detection

This project teaches image acquisition, preprocessing, coordinate systems, thresholds, overlays, latency, testing, and lifecycle management. Those skills carry into object detection. The new ingredient is semantic inference: a trained model estimates which learned categories are present and where.

A pretrained detector may recognize a stationary chair in a single image, because it uses learned visual features rather than requiring adjacent-frame change. Its capabilities are limited to its training/classes and operating conditions. A detected “person” class does not identify that individual.

Object-detection output commonly contains:

```text
class label: "chair"
score: 0.82
box: (x1, y1, x2, y2)
```

This is an illustrative prediction format, not current app output. A score is not automatically a calibrated probability or a guarantee of correctness. Class IDs, coordinate order, normalized versus pixel coordinates, and score meanings depend on the model/API.

## 22. Essential concepts for the next project

### Training versus inference

Training learns parameters from examples and annotations. Inference uses learned parameters on new inputs. Begin with pretrained inference so students can understand inputs/outputs before building a custom dataset. No trained model is part of this motion app.

### Preprocessing and coordinate restoration

A detector may require RGB, floating-point normalization, resizing, or letterboxing. Follow its documented contract rather than guessing. If an image is resized/padded, predicted coordinates must be mapped back to the original image before drawing. Color conversion must be performed exactly where required, not repeatedly.

### Confidence filtering and duplicate boxes

A score threshold discards weak predictions. Higher thresholds often reduce false positives but can miss real objects. Some detector pipelines use non-maximum suppression (NMS) to remove overlapping predictions; other architectures have different postprocessing. Do not apply NMS blindly when a model wrapper already performs it.

### Intersection over Union (IoU)

\[
IoU(A,B)=\frac{\operatorname{area}(A\cap B)}{\operatorname{area}(A\cup B)}.
\]

Example: boxes A=(0,0,10,10) and B=(5,0,15,10) under a continuous-coordinate convention have areas 100 each, intersection 50, union 150, so IoU=1/3. Explain the chosen coordinate convention; it differs from inclusive raster endpoints in drawing code.

### Precision, recall, and evaluation

Precision = TP/(TP+FP). Recall = TP/(TP+FN). A true-positive object prediction requires the correct class and adequate localization under the evaluation's matching rule; duplicates can be false positives. Specify zero-denominator handling when implementing metrics.

Example: 8 true positives, 2 false positives, 4 false negatives give precision 0.8 and recall 8/12, approximately 0.667. Average precision summarizes a precision-recall relationship under a defined evaluation protocol; mAP aggregates AP over classes and sometimes IoU thresholds. Always state the protocol before comparing numbers.

### Detection versus tracking

Detection answers what/where for an image. Tracking associates detections over time. A track ID is not a real-world identity, and reliable tracking needs additional logic. This app's changed-region boxes do not have tracking IDs.

## 23. A step-by-step first object-detection experiment

This is a future learning plan, not an implemented extension or a runnable framework API example.

1. Define a modest task and category set: for example, locating a small set of non-sensitive everyday objects in sample images.
2. Create a separate project/venv. Check the selected framework's currently supported Python versions, OS, hardware, installation instructions, and model license. Do not assume this app's Python 3.14 environment is supported by every inference framework.
3. Select a pretrained detector from maintained official documentation. Record framework/model version, weights source, class list, license, input contract, and whether processing is local. No specific “latest/best” model is prescribed here.
4. Begin with non-sensitive licensed still images and local inference. Confirm required BGR/RGB conversion, input dimensions, normalization, and output coordinate format.
5. Inspect boxes, labels, and scores before adding UI. Map boxes to original coordinates and distinguish model postprocessing from your own.
6. Test both positive and negative examples, multiple objects, small/occluded objects, and confusing backgrounds. Record ground truth and evaluation rules rather than judging only an impressive screenshot.
7. Profile model inference and end-to-end work separately. Start with documented CPU support; evaluate accelerators only when compatible and needed.
8. Add webcam capture only after still-image inference works. Reuse the motion project's separation and cleanup ideas, not its difference algorithm as a semantic detector.
9. Document failure modes, licenses, privacy, downloads, supported environments, and test evidence.
10. Consider fine-tuning only when pretrained categories/behavior do not meet the task. Curate annotations, separate training/validation/test data, prevent leakage, and keep held-out evaluation honest.

Conceptual pipeline:

```text
Input image -> Validate -> Model-specific preprocessing
            -> Pretrained model inference
            -> Documented postprocessing
            -> Class + score + restored box
            -> Draw on copy -> Display -> Cleanup
```

The following is pseudocode only; these are placeholders, not callable library APIs:

```text
load a verified pretrained model once
for each valid image:
    prepare according to that model's contract
    infer predictions
    use documented filtering/postprocessing
    restore coordinates to original image
    draw labels and boxes on a copy
```

Loading weights every frame would add needless work. Filtering webcam regions through motion first can miss stationary objects; it is not a universal replacement for full-image inference. Adding a learned detector changes scope and must be planned separately from version 1.

# Part VI - Revision and exercises

## 24. Common misconceptions

- “Every box is a recognized object.” A changed-region box has no semantic class.
- “No motion means the scene is empty.” Stationary objects can remain present.
- “More blur always improves results.” It can erase useful changes.
- “Area equals the count of white pixels.” Contour area is geometric and can differ.
- “Frozen dataclass means every nested item is immutable.” A nested list remains mutable.
- “Type hints reject bad inputs.” Runtime validation is still required.
- “Passing unit tests proves webcam support.” Hardware/window checks remain separate.
- “A high model score guarantees truth.” Scores and calibration are model-dependent.
- “waitKey(1) sets a guaranteed FPS.” It services events and has backend-dependent timing.

## 25. Review questions and answer guidance

1. Why does the first frame not alert? **No previous prepared frame exists; it establishes the baseline.**
2. Why use absdiff? **Absolute differences safely handle both directions of change without naive uint8 subtraction wrapping.**
3. What happens for difference 25 at threshold 25? **Mask value 0 because the boundary is strict >.**
4. Why can a still object stop alerting? **Consecutive stable frames become similar; presence is not the same as motion.**
5. What does opening do? **Erode then dilate, often removing small isolated foreground regions.**
6. Why render on a copy? **To keep changing overlays out of future comparisons.**
7. Why inject a clock? **Deterministic timing tests without sleeping; monotonic time measures durations safely.**
8. What if cleanup fails while read already failed? **Attempt both resources and preserve the original failure.**
9. How does increased resolution affect minimum area? **The same physical region can cover more pixels, so sensitivity needs recalibration.**
10. What must be added for object detection? **A documented trained-model inference pipeline with classes/scores and proper preprocessing/postprocessing.**
11. Why use a separate object-detection venv? **Its framework may require different Python/dependency compatibility.**
12. Calculate IoU for two area-100 boxes with overlap 50. **50/(100+100-50)=1/3.**

## 26. Glossary

| Term | Meaning |
| --- | --- |
| Frame | One image in a video sequence |
| BGR | Blue-green-red channel order |
| uint8 | Unsigned 8-bit integer, values 0-255 |
| Baseline | Previous prepared frame used for comparison |
| Kernel | Neighborhood weights or structuring element |
| Binary mask | Two-valued pixel image describing a condition |
| Contour | Boundary representation of an image region |
| Bounding box | Rectangle enclosing a region/prediction |
| Morphology | Shape operations on a mask |
| Monotonic clock | Clock suitable for elapsed duration measurement |
| Dependency injection | Providing replaceable collaborators externally |
| Inference | Running learned parameters on a new input |
| Ground truth | Reference annotations used for evaluation |
| IoU | Intersection area divided by union area |
| False positive | An incorrect positive detection under the chosen rule |
| False negative | A missed reference event/object under the chosen rule |

## 27. Source provenance and PDF accuracy checklist

The educational manuscript is based on this project's architecture, development plan, README, source modules, test suite, and validation report. The embedded code below is the actual local snapshot at preparation time. Regenerate it if code changes before producing another edition.

For PDF review: verify author spelling, equations, BGR/RGB distinction, threshold > versus area >=, first/reset-frame behavior, stopped-object behavior, current-only boxes, hold expiry, CLI spellings, venv paths, dependency versions, and validation limitations. Ensure conceptual object-detection examples are not presented as app features. Do not substitute invented source for the appendix.

# Appendix A - Complete application and dependency snapshot

The code below is verbatim application source and configuration from this edition. Treat long-line wrapping as typesetting only. Explain imports, classes, methods, conditionals, library calls, and error paths in the corresponding chapter.

## pyproject.toml

```toml
[build-system]
requires = ["setuptools==84.0.0"]
build-backend = "setuptools.build_meta"

[project]
name = "webcam-motion-app"
version = "0.1.0"
description = "Local in-memory webcam motion detection"
readme = "README.md"
requires-python = ">=3.14"
dependencies = ["numpy==2.5.3", "opencv-python==5.0.0.93"]

[project.optional-dependencies]
dev = ["pytest==9.1.1"]

[project.scripts]
motion-app = "motion_app.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
filterwarnings = ["error"]
```

## requirements-dev.txt

```text
# Tested complete development environment; install inside venv.
numpy==2.5.3
opencv-python==5.0.0.93
pytest==9.1.1
iniconfig==2.3.0
packaging==26.3
pluggy==1.6.0
Pygments==2.21.0
setuptools==84.0.0
wheel==0.48.0
```

## src/motion_app/__init__.py

```python
"""Local, in-memory webcam motion detection."""

__version__ = "0.1.0"
```

## src/motion_app/config.py

```python
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
```

## src/motion_app/preprocessing.py

```python
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
```

## src/motion_app/camera.py

```python
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
```

## src/motion_app/motion_detector.py

```python
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
```

## src/motion_app/display.py

```python
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
```

## src/motion_app/app.py

```python
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
```

## src/motion_app/main.py

```python
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
```

## src/motion_app/__main__.py

```python
"""Enable python -m motion_app."""

from .main import main

raise SystemExit(main())
```

# Appendix B - Representative executable tests

These verbatim tests illustrate controlled inputs, exact boundaries, and fake clocks. The full project suite additionally covers lifecycle and adapter failures.

## tests/test_motion_detector.py

```python
import numpy as np
import pytest
from motion_app.config import Config
from motion_app.motion_detector import MotionDetector


def frame():
    return np.zeros((120, 160, 3), np.uint8)


def test_first_quiet_movement_stopped_and_reset():
    detector = MotionDetector(Config())
    quiet = frame()
    assert detector.process(quiet).baseline_reset
    assert not detector.process(quiet).motion
    changed = quiet.copy()
    changed[30:70, 40:90] = 255
    result = detector.process(changed)
    assert result.motion and len(result.boxes) == 1
    x, y, w, h = result.boxes[0]
    assert x <= 40 and y <= 30 and x + w >= 90 and y + h >= 70
    assert not detector.process(changed).motion
    assert detector.process(np.zeros((50, 50, 3), np.uint8)).baseline_reset
    detector.reset()
    assert detector.process(quiet).baseline_reset


def test_noise_filtered_and_multiple_regions():
    detector = MotionDetector(Config())
    quiet = frame()
    detector.process(quiet)
    noisy = quiet.copy()
    noisy[10, 10] = 255
    assert not detector.process(noisy).motion
    noisy[20:50, 20:50] = 255
    noisy[70:105, 110:145] = 255
    assert len(detector.process(noisy).boxes) == 2


@pytest.mark.parametrize('pixel,motion', [(25, False), (26, True)])
def test_threshold_strictly_greater(pixel, motion):
    detector = MotionDetector(Config(blur_kernel=1, morphology_kernel=1, min_area=1))
    quiet = frame()
    detector.process(quiet)
    changed = quiet.copy()
    changed[10:20, 10:20] = pixel
    assert detector.process(changed).motion == motion


@pytest.mark.parametrize('area,motion', [(81, True), (81.1, False)])
def test_contour_area_inclusive(area, motion):
    # A 10x10 filled pixel block has geometric contour area 9x9, not 100.
    detector = MotionDetector(Config(blur_kernel=1, morphology_kernel=1, min_area=area))
    quiet = frame()
    detector.process(quiet)
    changed = quiet.copy()
    changed[10:20, 10:20] = 255
    original = changed.copy()
    assert detector.process(changed).motion == motion
    np.testing.assert_array_equal(changed, original)
```

## tests/test_alert_state.py

```python
from motion_app.app import AlertState
from motion_app.motion_detector import DetectionResult


def test_hold_refresh_expiry_and_reset():
    now = [1.0]
    state = AlertState(0.5, lambda: now[0])
    quiet = DetectionResult(False, [])
    motion = DetectionResult(True, [(0, 0, 1, 1)])
    assert not state.update(quiet)
    assert state.update(motion)
    now[0] = 1.25
    assert state.update(quiet)
    assert state.update(motion)
    now[0] = 1.75
    assert not state.update(quiet)
    assert state.update(motion)
    assert not state.update(DetectionResult(False, [], True))
    assert not state.update(quiet)


def test_zero_hold():
    state = AlertState(0, lambda: 1.0)
    assert state.update(DetectionResult(True, []))
    assert not state.update(DetectionResult(False, []))
```

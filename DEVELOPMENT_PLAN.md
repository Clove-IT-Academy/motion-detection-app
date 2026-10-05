# Motion Detection App: Development Plan

Status: version 0.1.0 implementation candidate complete; camera-independent validation passed; real-camera acceptance pending permission and manual checks (2026-10-05).
Created: 2026-10-04.
Source: [Motion Detection System Architecture](Motion_Detection_System_Architecture.pdf), all six pages, sections 1-9.

## 1. Purpose and how to use this plan

Build a local Python/OpenCV desktop application that opens one webcam, detects sufficiently visible movement between consecutive frames, and displays a clear motion status. This document turns the architecture into an ordered implementation and verification plan. Use it together with the architecture as context for future development sessions.

Work through the steps in order. Finish each step's exit criteria before moving to the next dependent step. Keep changes small and reviewable. Update the progress checklist, decision log, and validation evidence as work is completed. A checkbox means implementation and its required checks are complete, not merely that files were created.

The architecture defines product requirements. Defaults, interfaces, file names beyond its example, and workflow choices below are proposed implementation decisions. Revise them when evidence warrants it and record the reason. If a future request changes product scope, update both the affected requirements and this plan before implementing the change.

### Current project baseline

Original planning baseline (2026-10-04): architecture PDF, `.gitignore`, local `venv/`, and Git metadata only. As of 2026-10-05, the source package, pinned dependencies, README, tests, and validation/release checklists are implemented. Fresh-venv installation is verified. Preserve the architecture and existing user files.

## 2. Version 1 scope and acceptance requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| R1 | Open one configured camera and show its live preview | Manual camera and permission checks on every claimed platform |
| R2 | Compare consecutive prepared frames; filter changed regions by pixel threshold and contour area | Synthetic detector tests and live near/far movement checks |
| R3 | Show `Motion detected!` or `No motion detected`; hold the alert briefly to reduce flicker | Fake-clock timing tests and manual stop/start checks |
| R4 | Optional boxes around qualifying regions; readable status and exit hint | Display checks on bright/dark scenes and small frames |
| R5 | Quit using a key or the window close control | Automated lifecycle tests and manual platform checks |
| R6 | Handle unavailable camera, failed/invalid reads, and processing/display errors cleanly | Failure injection and resource cleanup assertions |
| R7 | Keep frames in memory; do not store or transmit video or include frames in logs | Source review and runtime check of app-created files |
| R8 | Maintain separate capture, preprocessing, detection, display, configuration, and controller responsibilities | Module review and camera-free automated tests |
| R9 | Provide reproducible setup, tested dependencies, limitations, release identity, and maintenance guidance | Fresh-environment installation and student handoff check |
| R10 | Measure responsiveness on target hardware | Recorded settings, environment, timings, and live usability observations |

Excluded from version 1: object/person recognition, face analysis, movement classification, recording, screenshots, uploads, analytics, accounts, server, database, multiple simultaneous cameras, trained models, and background subtraction. Do not promise detection of every movement: small or slow changes, noise, lighting, camera motion, and scene contrast affect results.

## 3. Planned technical decisions

### Runtime and delivery

- One process and one OpenCV preview window. Start with a synchronous frame loop; introduce concurrency only if measurements demonstrate a need.
- Use Python, NumPy, and GUI-enabled OpenCV. Use pytest for automated tests. Do not use a headless OpenCV distribution for the desktop runtime or install competing OpenCV variants in one environment.
- Use `pyproject.toml`, a `src/` package, and a documented dependency lock or exact tested pins. Select Python and library versions during setup after verifying installation and GUI operation; this plan does not assert untested version compatibility.
- First delivery is a source installation with a command-line entry point. Executable packaging is a later, separately validated option.
- Verify macOS first because the current workspace is on macOS. Treat Windows/Linux support as unverified until separately tested. Keep the implementation portable where practical.
- Use command-line configuration initially. Interactive sensitivity keys are deferred; camera selection through an index is supported without building a selection UI.

### Proposed initial configuration

These values are starting points for calibration, not architecture-mandated values or proven optimal settings.

| Setting | Initial value | Validation and interpretation |
| --- | --- | --- |
| Camera index | `0` | Nonnegative integer; device availability checked when opening |
| Pixel-change threshold | `25` | Integer 0-255; changed pixels must exceed it |
| Minimum contour area | `500` | Positive pixel area; contours with area at least this value qualify |
| Gaussian blur kernel | `5 x 5` | Positive odd dimensions; operate on grayscale |
| Morphology kernel | `3 x 3` | Positive odd dimensions; proposed opening then closing, one iteration each |
| Alert hold time | `0.5 seconds` | Finite nonnegative value; use a monotonic clock |
| Show region boxes | `true` | Boolean; disabling boxes does not change detection |
| Quit controls | `q` and `Esc` | Window close must also exit |
| Capture resolution | Camera default | Record actual dimensions; do not silently assume a requested size was accepted |

Do not resize frames in the initial implementation. Pixel-area thresholds therefore depend on actual resolution; document this and recalibrate when resolution changes. Tune morphology with synthetic and real scenes: too much cleanup can erase useful movement.

### Behavioral rules

1. The first valid frame establishes the baseline and produces no motion alert.
2. Validate a frame before conversion. A failed read, missing frame, empty array, or unsupported format ends the run with an actionable error; do not process stale data or silently retry indefinitely.
3. Prepare the image, compute absolute difference from the previous prepared image, threshold, clean the mask, extract external contours, filter by area, and produce bounding boxes.
4. Always advance the previous-frame baseline after a valid comparison. Never feed annotated display images into the detector.
5. A changed frame size resets the baseline and produces no detection for that frame. Clear alert timing too, so old state does not survive the reset.
6. Raw detection and displayed alert are separate. Any qualifying contour refreshes the last-motion timestamp. With no new detection, retain the alert only while elapsed time is less than the hold duration; at expiry show quiet status. Zero hold means no persistence.
7. Draw only boxes from the current detector result, even while the message remains held. Do not show stale boxes as current detections.
8. An object that stops moving stops triggering raw detection once adjacent frames stabilize. The held message then expires.
9. Lighting changes and camera shake may trigger motion. Document them as limitations; do not add unproven suppression that conceals movement.
10. Guaranteed cleanup covers partial startup, normal exit, interruption, and failures. Release the camera and attempt window destruction independently, even if one cleanup action fails.

## 4. Target code organization and component contracts

```text
motion-detection-app/
  Motion_Detection_System_Architecture.pdf
  DEVELOPMENT_PLAN.md
  README.md
  pyproject.toml
  <dependency lock file or tested pins>
  src/motion_app/
    __init__.py
    __main__.py
    main.py
    app.py
    camera.py
    preprocessing.py
    motion_detector.py
    display.py
    config.py
  tests/
    test_config.py
    test_preprocessing.py
    test_motion_detector.py
    test_alert_state.py
    test_app_flow.py
    test_display.py
  docs/
    MANUAL_TEST_CHECKLIST.md
    VALIDATION_RESULTS.md
    RELEASE_CHECKLIST.md
```

| Component | Planned contract and ownership |
| --- | --- |
| `config.py` | Validated configuration with defaults; reject invalid inputs before camera access |
| `camera.py` | `open()`, `read()`, `release()`; adapter owns capture handle and reports explicit camera errors |
| `preprocessing.py` | Prepare a valid BGR frame into blurred grayscale; no camera, GUI, or disk I/O |
| `motion_detector.py` | Stateful `process(frame)` and `reset()`; owns previous prepared frame; returns motion flag, current boxes, and baseline/reset indication |
| `display.py` | Render on a copy, show preview, poll quit/window events, close window; no detector or camera state |
| `app.py` | Own lifecycle and alert timing; coordinate adapters; accept fake camera, display, and clock for tests |
| `main.py` / `__main__.py` | Parse options, build components, report concise operational errors, and return exit codes |

Use a small structured result for detection: `motion: bool`, `boxes: list[(x, y, width, height)]`, and `baseline_reset: bool`. A baseline reset includes the first frame. Keep masks/contours internal unless a real test or profiling need warrants exposing them. Inject the monotonic clock into alert-state logic; tests must not sleep.

Planned exit codes: `0` for user-requested normal shutdown, `1` for runtime camera/processing/display failure, `2` for invalid CLI configuration. Document interruption behavior consistently. Do not swallow unexpected exceptions and report success.

## 5. Step-by-step implementation sequence

### Step 1 - Establish the project and development environment

Dependencies: none.

1. Inspect existing files and Git state; preserve user changes and exclude `venv/` and generated outputs.
2. Select and record a tested Python version. Check the existing environment before reusing it; make a fresh environment reproducible from declared dependencies.
3. Create package metadata, the source skeleton, pytest configuration, runtime dependencies, and development dependencies.
4. Define the module/console entry point and a minimal help command. Avoid opening the camera during imports or help output.
5. Add basic README setup/run/test instructions and document the local-only scope.
6. Verify editable installation, imports, help, and test discovery from a clean environment.

Deliverables: package skeleton, dependency manifest and reproducible pins/lock, initial README.

Exit criteria: another developer can install declared dependencies and invoke help; imports have no device or GUI side effects. Record exact Python/OpenCV/NumPy versions actually tested.

### Step 2 - Implement validated configuration

Dependencies: Step 1.

1. Implement defaults and CLI options for camera index, threshold, minimum area, hold time, and boxes.
2. Validate numeric ranges, finite timing values, and odd kernel dimensions. Avoid accepting NaN or infinity as valid settings.
3. Keep blur/morphology settings centralized; expose additional CLI controls only when needed.
4. Document pixel-area/resolution dependence and sensitivity tradeoffs.
5. Test valid defaults, overrides, boundary values, and rejected configurations.

Deliverables: `config.py`, CLI parsing, configuration tests and documentation.

Exit criteria: invalid configuration produces an understandable error before any camera/window is opened; defaults are documented and testable.

### Step 3 - Deliver a working webcam preview

Dependencies: Steps 1-2.

1. Implement the camera adapter and readiness check.
2. Validate every read result and frame before display or processing.
3. Implement one named preview window, event polling, and `q`/`Esc` exit.
4. Detect window close using behavior verified on the target OpenCV GUI backend. Handle property-query errors without recreating a closed window.
5. Put acquisition and preview inside a guaranteed cleanup path from the beginning.
6. Handle unavailable camera, denied permission, failed read, GUI startup failure, and keyboard interruption.
7. Use fake adapters to test startup/read/exit flow and cleanup, then test a real camera locally.

Deliverables: camera/display/controller preview path and lifecycle tests.

Exit criteria: continuous live preview works; all three exit controls release the camera; startup/read failure does not hang or process invalid images. Another process can reopen the camera after exit.

### Step 4 - Implement preprocessing and motion detection in isolation

Dependencies: Step 2; integrate only after Step 3 is stable.

1. Convert validated BGR frames to grayscale and apply light Gaussian blur.
2. Establish baseline state without triggering detection.
3. Compute absolute frame difference and binary threshold mask.
4. Apply proposed morphological opening/closing; tune against test cases.
5. Extract external contours, filter by contour area, and return bounding rectangles.
6. Update the baseline after every valid frame and implement reset on shape change.
7. Build deterministic synthetic tests for identical images, a sufficiently large changed block, tiny noise, multiple regions, stopped movement, threshold/area boundaries, reset, and invalid frames.
8. Ensure input frames remain unmodified and tests do not require a camera/window.

Deliverables: preprocessing module, detector, structured detection result, unit tests.

Exit criteria: expected frame sequences produce correct flags and regions, noise is filtered, and first/reset frames do not alert. Boundary tests explicitly cover threshold `>` and area `>=` semantics. Account for blur/morphology when designing fixtures rather than assuming raw block size equals final contour area.

### Step 5 - Implement alert timing and integrate the full pipeline

Dependencies: Steps 3-4.

1. Add last-motion timing using a monotonic clock, separate from the detector.
2. Integrate read -> validate -> preprocess/detect -> update alert -> render -> show -> poll controls.
3. Render the two specified status messages, optional current-region boxes, and an exit hint.
4. Use high-contrast text with a background panel; do not depend on color alone or obstruct the main image.
5. Adapt text layout to small frame sizes. Keep drawing on a display copy so overlays cannot create false detections.
6. Clear alert state on baseline resets and keep held alerts independent from current boxes.
7. Test alert refresh, exact expiry, zero hold, repeated movement, quiet recovery, and reset using a fake clock.
8. Check startup, movement, and quiet behavior with the real camera.

Deliverables: complete version 1 behavior, alert-state tests, overlay checks.

Exit criteria: movement alerts immediately; the message remains for the configured duration after the last detection; stopped movement returns to quiet; overlays do not alter detector inputs.

### Step 6 - Harden failure handling and privacy

Dependencies: Step 5.

1. Inject failures during camera open, first/subsequent reads, preprocessing, detection, display, event polling, and cleanup.
2. Assert camera release and window cleanup for partial startup, all quit paths, and errors.
3. Make cleanup safe when called after partial initialization or more than once; attempt both resources even if one operation raises.
4. Provide concise errors with practical checks for index, permissions, camera usage, and desktop GUI availability.
5. Review all logging and filesystem/network behavior. Do not add frame dumps, recording, frame-containing exception attachments, or telemetry.
6. Confirm runtime memory is bounded: retain only the previous prepared frame and current working arrays, not a frame history or unbounded results.
7. Verify exit codes and avoid masking the original runtime failure with cleanup errors.

Deliverables: failure-path tests, operational messages, documented privacy behavior.

Exit criteria: injected failures never process invalid frames or leave resources intentionally open; logs contain operational metadata only; the app has no video persistence or transmission path.

### Step 7 - Calibrate sensitivity and validate responsiveness

Dependencies: Step 6.

1. Create a repeatable manual checklist with camera placement, scene, lighting, actual resolution, and settings.
2. Test a steady scene, visible near/far movement, small movement, multiple changed regions, and movement followed by complete stillness.
3. Test camera bump and gradual/abrupt lighting changes; record limitations rather than promise their elimination.
4. Adjust threshold, minimum area, blur, morphology, and hold duration based on recorded results. Update defaults, tests, and README together.
5. Measure processing time and overall loop/display responsiveness with aggregate numeric metrics only. Record hardware, OS, dependency versions, sample duration, and actual dimensions.
6. Observe quit responsiveness during normal movement and error scenarios. If a backend blocks during reads, document the observed behavior and investigate before claiming responsive shutdown.
7. Optimize only measured bottlenecks; preserve correctness and privacy. Avoid a fixed FPS claim without supporting measurements.

Deliverables: calibrated defaults and `docs/VALIDATION_RESULTS.md` with measured evidence.

Exit criteria: representative visible movement is detected, normal scene noise is acceptably filtered under recorded conditions, alert flicker is controlled, and the preview/controls are usable on the tested machine. Document any conditions that fail.

### Step 8 - Complete automated and platform acceptance checks

Dependencies: Step 7.

1. Run the full automated suite from a fresh environment; camera-free tests must run without real webcam access.
2. Complete the manual matrix below on each platform claimed as supported.
3. Retest detection after calibration and resource behavior after failures.
4. Mark each requirement R1-R10 as passed, failed, or unverified with evidence.
5. Fix release-blocking failures and rerun the affected checks. Keep untested platforms explicitly unverified.
6. Optionally add CI for the camera-free suite once the local workflow is stable; GUI/camera checks remain manual.

Deliverables: completed manual checklist, automated results, requirement acceptance record.

Exit criteria: every version 1 requirement has evidence on the supported target; no known release-blocking issue remains. Do not use passing unit tests as proof of webcam permission or native window behavior.

### Step 9 - Prepare release and student handoff

Dependencies: Step 8.

1. Finalize README installation, environment activation, run examples, all controls/options, test instructions, and troubleshooting.
2. Document frame differencing behavior, sensitivity/resolution dependence, lighting/camera-shake limitations, and in-memory processing.
3. Assign a version identifier and state which OS/Python/dependency/camera combinations were tested.
4. Provide a short demo script: launch -> quiet scene -> movement -> stop and observe expiry -> quit -> confirm camera can reopen.
5. Verify installation and execution by following documentation in a fresh environment, preferably with another student.
6. Complete a release checklist and specify who maintains the repository; owner assignment remains open until a person is named.
7. Review source, dependencies, tests, and docs before creating a release/tag when requested. Do not include the environment, local media, or generated diagnostic data.

Deliverables: usable source release, setup/demo instructions, limitations, validation record, maintenance ownership.

Exit criteria: another student can install and run the app using only the handoff documentation, and the released version matches the validated code and dependency set.

### Step 10 - Maintain and assess future changes

Dependencies: released version 1.

1. Collect issue reports containing version, OS, camera model if known, configuration, reproduction steps, and error text. Do not request webcam footage by default.
2. Reproduce with synthetic frames or non-sensitive metadata when possible.
3. Review dependency changes and retest GUI/camera behavior after updates.
4. Consider interactive controls, a camera picker, a background model, or executable packaging only after a documented need.
5. For packaging, build and verify on each intended OS, including camera permission and OpenCV window behavior; source-release success does not validate an executable.
6. Revisit product/privacy scope before any recording, screenshots, uploads, or analytics feature.

Exit criteria for each maintenance change: updated decisions, appropriate regression evidence, and release notes describing the user-visible effect.

## 6. Required validation matrix

| Scenario | Automated evidence | Manual evidence |
| --- | --- | --- |
| First valid frame | No raw motion; baseline recorded | No startup false alert |
| Identical consecutive frames | No qualifying regions | Quiet scene remains quiet under recorded lighting |
| Large visible change | Motion and sensible bounding boxes | Near/far movement alerts |
| Tiny isolated changes | Filtered by cleanup/area | Ordinary sensor noise does not cause persistent alerts |
| Stopped object | Raw detection ceases on stable frame pair | Held alert expires without excessive flicker |
| Hold timing | Fake-clock expiry, refresh, and zero hold | Message is readable and quiet recovery sensible |
| Changed frame shape | Baseline/alert reset; no shape mismatch | Check if camera/backend changes resolution |
| Camera unavailable/permission denied | Fake open failure and cleanup | Actionable message, clean exit |
| Failed/invalid read | No downstream processing; cleanup | Disconnect/failure where practical |
| Quit and window close | Simulated exit events, cleanup assertions | `q`, `Esc`, close control, camera reuse |
| Processing/display exception | Failure injection, nonzero exit, cleanup | GUI backend availability/error behavior |
| Lighting/camera movement | Optional synthetic global change characterization | Record false alerts and limitations |
| Accessibility | Overlay input preservation and layout checks | Bright/dark backgrounds and small preview |
| Privacy and bounded memory | Review I/O and retained state | No app-generated video/images; stable extended run |
| Installation and performance | Fresh environment suite | Fresh install, measured loop responsiveness and demo |

Use generated arrays for fixtures. Distinguish genuinely small noise from blur-expanded regions. Do not add personal camera footage to source control. Operational measurements may contain counts/timings/settings but never image pixels.

## 7. Milestones and progress tracking

There is no committed calendar estimate: camera/backend behavior and target-platform availability affect effort. The gates below define completion more reliably than dates.

- [x] M1: Reproducible foundation and configuration - Steps 1-2.
- [ ] M2: Reliable camera preview and exit - Step 3.
- [x] M3: Camera-independent detector passes synthetic tests - Step 4.
- [ ] M4: Complete motion UI and alert timing - Step 5.
- [ ] M5: Failure handling and privacy verified - Step 6.
- [ ] M6: Calibrated and measured on target hardware - Step 7.
- [ ] M7: Automated/platform acceptance complete - Step 8.
- [ ] M8: Student-ready version 1 release and handoff - Step 9.
- [ ] M9: Maintenance owner and process established - Step 10.

For each completed milestone record: implementation revision, delivered files, checks executed, environment, results, limitations, and the next step. The step descriptions specify required checks. See `docs/VALIDATION_RESULTS.md` for executed checks and their limits; unchecked milestones still have outstanding acceptance criteria.

## 8. Open decisions and risk handling

| Item | Proposed handling | Resolve by |
| --- | --- | --- |
| Python/dependency versions | Choose installed/tested compatible versions and freeze them | Step 1 |
| Supported operating systems | Validate macOS first; add claims only with evidence | Steps 1 and 8 |
| Optimal sensitivity/morphology | Start with listed proposals, tune on target camera | Step 7 |
| Window-close behavior differs by backend | Isolate event handling, verify native close, avoid window recreation | Steps 3 and 8 |
| Camera permissions/device contention | Clear startup messages and manual permission checks | Steps 3 and 8 |
| Read may block on a backend | Measure quit behavior; investigate backend-specific handling if needed | Step 7 |
| Frame rate affects adjacent-frame changes | Record actual behavior and avoid universal sensitivity claims | Step 7 |
| Lighting and camera shake cause alerts | Document limitation; background model is a future option | Steps 7 and 9 |
| Pixel-area setting depends on resolution | Record actual dimensions and explain recalibration | Steps 2 and 7 |
| Release owner | Name maintainer before handoff is considered complete | Step 9 |
| Executable distribution | Deferred; source installation is version 1 delivery | After version 1 |

Decision log template:

```text
Date / milestone:
Decision:
Reason and supporting evidence:
Affected requirements/modules:
Validation required:
```

## 9. Instructions for future development sessions

Read the architecture PDF and this plan before implementing. Inspect actual source, repository instructions, and Git state; do not assume that planned files already exist or that checklist status is current. Start with the earliest incomplete milestone and implement its concrete tasks and exit checks. Preserve module boundaries and the local-only privacy scope. Record tested versions rather than choosing dependency versions from memory.

Report what changed, what checks actually passed, what remains unverified, and which milestone comes next. Update this document when a decision or milestone changes. Do not add unrelated features to complete a step. Avoid recording/uploading webcam content for debugging. Keep hardware/platform validation honest and separate from camera-free automated evidence.

## 10. Implementation update - 2026-10-05

Version 0.1.0 implements Steps 1-6 source behavior and the documentation for
Steps 7-10. M1 and M3 are complete: reproducible environment/configuration and
synthetic detector checks passed. Other milestones remain open where their
exit criteria require real-camera or student validation. Do not interpret the
implemented source as full hardware acceptance.

Decisions:
- Reuse project venv with Python 3.14.7; pin latest compatible stable OpenCV
  Python 5.0.0.93, NumPy 2.5.3, and pytest 9.1.1. Fresh venv checks passed.
- Require Python >=3.14 for this tested source candidate; older versions are
  not claimed as supported. Desktop webcam compatibility is still pending.
- Keep planned defaults and algorithm; calibration remains pending. Bound
  internal odd kernel sizes to 31 and capture to 32 megapixels/8192 per axis
  before native processing to reject malformed frames without excessive work.
- Reject Wayland because OpenCV cannot fulfill window-close inspection there.
  A property error after polling is treated as native close, matching backends
  that throw on destroyed windows. Manual backend validation remains necessary.
- Treat Ctrl+C as normal user shutdown (exit 0); runtime/cleanup failures exit 1.
- Native Cocoa synthetic preview passed. Camera-index-0 smoke was blocked by
  macOS camera authorization; no real-camera acceptance is claimed.

Delivered: src/motion_app, tests, pyproject.toml, requirements-dev.txt, README,
manual checklist, validation record, and release checklist. Next gate: grant
camera permission and complete real-camera calibration/quit/resource checks.
Maintenance owner and another-student handoff remain open.
